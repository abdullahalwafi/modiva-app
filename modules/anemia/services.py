import base64
import io
import re
import traceback
from functools import lru_cache
from pathlib import Path

from django.conf import settings


SELECTED_FEATURES = ['HGB', 'HCT', 'RBC', 'MCH', 'MCHC']


class AnemiaPredictionError(Exception):
    pass


def _import_ml_dependencies():
    try:
        import cloudpickle
        import joblib
        import lime.lime_tabular
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import shap
    except ImportError as exc:
        raise AnemiaPredictionError(
            'Dependency ML anemia belum lengkap. Pastikan joblib, cloudpickle, shap, dan lime sudah terpasang.'
        ) from exc

    return cloudpickle, joblib, lime, plt, np, pd, shap


@lru_cache(maxsize=1)
def load_assets():
    cloudpickle, joblib, lime, plt, np, pd, shap = _import_ml_dependencies()
    asset_dir = Path(settings.BASE_DIR) / 'modules' / 'anemia' / 'ml_assets'

    try:
        with open(asset_dir / 'best_model_update.pkl', 'rb') as file:
            model = cloudpickle.load(file)
        scaler = joblib.load(asset_dir / 'scaler.pkl')
        x_train = joblib.load(asset_dir / 'X_train.pkl')
        x_train_scaled = joblib.load(asset_dir / 'X_train_scaled.pkl')
    except FileNotFoundError as exc:
        raise AnemiaPredictionError('Asset model anemia belum lengkap di modules/anemia/ml_assets.') from exc

    x_train_selected = x_train[SELECTED_FEATURES]

    try:
        if x_train_scaled is not None:
            background = (
                x_train_scaled
                if isinstance(x_train_scaled, (np.ndarray, pd.DataFrame))
                else scaler.transform(x_train_selected)
            )
        else:
            background = scaler.transform(x_train_selected)
    except Exception:
        background = scaler.transform(x_train_selected)

    if len(background) > 100:
        background = shap.sample(background, 100, random_state=42)

    def model_predict_scaled(x_scaled):
        return model.predict_proba(x_scaled)

    explainer = shap.KernelExplainer(model_predict_scaled, background)
    return {
        'model': model,
        'scaler': scaler,
        'x_train': x_train,
        'background': background,
        'explainer': explainer,
        'deps': {
            'lime': lime,
            'plt': plt,
            'np': np,
            'pd': pd,
            'shap': shap,
        },
    }


def predict_anemia(feature_values):
    assets = load_assets()
    model = assets['model']
    scaler = assets['scaler']
    pd = assets['deps']['pd']

    user_input = pd.DataFrame([[feature_values[feature] for feature in SELECTED_FEATURES]], columns=SELECTED_FEATURES)
    user_input_scaled = scaler.transform(user_input)
    prediction = model.predict(user_input_scaled)[0]
    probability = model.predict_proba(user_input_scaled)[0]

    class_order = list(model.classes_)
    probability_map = {}
    for index, class_value in enumerate(class_order):
        label = 'Anemia' if int(class_value) == 0 else 'Healthy'
        probability_map[label] = float(probability[index])

    if probability_map.get('Healthy', 0) >= probability_map.get('Anemia', 0):
        result = 'Healthy'
        shap_class_idx = int(assets['deps']['np'].where(model.classes_ == 1)[0][0]) if 1 in model.classes_ else 1
    else:
        result = 'Anemia'
        shap_class_idx = int(assets['deps']['np'].where(model.classes_ == 0)[0][0]) if 0 in model.classes_ else 0

    shap_plot, shap_summary = shap_waterfall_plot(assets, user_input_scaled, shap_class_idx)
    lime_plot, lime_summary = lime_html(assets, user_input)
    main_causes = get_main_causes(shap_summary, user_input)
    abnormal_count, abnormal_details = check_medical_status(user_input)

    return {
        'result': result,
        'prediction': int(prediction),
        'prob_anemia': probability_map.get('Anemia', 0),
        'prob_healthy': probability_map.get('Healthy', 0),
        'shap_plot': shap_plot,
        'lime_plot': lime_plot,
        'shap_summary': shap_summary,
        'lime_summary': lime_summary,
        'main_causes': main_causes,
        'abnormal_count': abnormal_count,
        'abnormal_details': abnormal_details,
        'interpret_text': generate_interpretation(result, probability_map, main_causes, abnormal_count),
        'summary_text': generate_summary(shap_summary, lime_summary, result),
        'input_values': feature_values,
    }


def shap_waterfall_plot(assets, user_input_scaled, class_idx=0):
    np = assets['deps']['np']
    plt = assets['deps']['plt']
    shap = assets['deps']['shap']
    explainer = assets['explainer']

    try:
        shap_values = explainer(user_input_scaled)
        values = shap_values.values if hasattr(shap_values, 'values') else shap_values

        if np.ndim(values) == 3:
            shap_single = values[0, :, class_idx]
            base_value = shap_values.base_values[0, class_idx]
        elif np.ndim(values) == 2:
            shap_single = values[0]
            base_value = shap_values.base_values[0] if hasattr(shap_values, 'base_values') else 0
        else:
            shap_single = values
            base_value = shap_values.base_values if hasattr(shap_values, 'base_values') else 0

        explanation = shap.Explanation(
            values=shap_single,
            base_values=base_value,
            data=user_input_scaled[0],
            feature_names=SELECTED_FEATURES,
        )

        fig = plt.figure(figsize=(8, 4.5))
        shap.plots.waterfall(explanation, show=False)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)

        return encoded, dict(zip(SELECTED_FEATURES, shap_single))
    except Exception:
        traceback.print_exc()
        return None, {}


def lime_html(assets, user_input):
    model = assets['model']
    scaler = assets['scaler']
    x_train = assets['x_train']
    lime = assets['deps']['lime']
    np = assets['deps']['np']

    try:
        x_train_selected = x_train[SELECTED_FEATURES]
        x_train_scaled = scaler.transform(x_train_selected)
        class_names_map = {0: 'Anemia', 1: 'Healthy'}
        class_names = [class_names_map.get(int(class_value), str(class_value)) for class_value in model.classes_]

        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=np.array(x_train_scaled),
            feature_names=SELECTED_FEATURES,
            class_names=class_names,
            mode='classification',
        )
        data_row = scaler.transform(user_input)[0]
        explanation = explainer.explain_instance(
            data_row=data_row,
            predict_fn=model.predict_proba,
            num_features=len(SELECTED_FEATURES),
        )

        html = explanation.as_html()
        lime_summary = {}
        for feature, value in re.findall(r'([A-Z]+)[^0-9\-]+([-]?\d+\.\d+)', html):
            lime_summary[feature] = float(value)

        encoded = base64.b64encode(html.encode()).decode('utf-8')
        return f'data:text/html;base64,{encoded}', lime_summary
    except Exception:
        traceback.print_exc()
        return None, {}


def check_medical_status(user_input):
    rules = {
        'HGB': (12.0, 16.0),
        'HCT': (36.0, 46.0),
        'RBC': (4.2, 5.4),
        'MCH': (27.0, 33.0),
        'MCHC': (32.0, 36.0),
    }
    abnormal = 0
    details = []

    for feature, (low, high) in rules.items():
        value = float(user_input.iloc[0][feature])
        if value < low:
            abnormal += 1
            details.append(f'{feature} rendah ({value:.2f})')
        elif value > high:
            abnormal += 1
            details.append(f'{feature} tinggi ({value:.2f})')

    return abnormal, details


def get_main_causes(shap_summary, user_input, top_n=5):
    feature_mapping = {
        'HGB': ('Hemoglobin', 12.0, 16.0),
        'HCT': ('Hematokrit', 36.0, 46.0),
        'RBC': ('Jumlah Sel Darah Merah', 4.2, 5.4),
        'MCH': ('MCH', 27.0, 33.0),
        'MCHC': ('MCHC', 32.0, 36.0),
    }
    sorted_features = sorted(shap_summary.items(), key=lambda item: abs(item[1]), reverse=True)
    causes = []

    for feature, _shap_value in sorted_features[:top_n]:
        actual_value = float(user_input.iloc[0][feature])
        feature_name, lower, upper = feature_mapping.get(feature, (feature, None, None))

        if lower is None:
            causes.append(f'{feature_name} = {actual_value:.2f}')
            continue

        if actual_value < lower:
            status = 'di bawah normal'
        elif actual_value > upper:
            status = 'di atas normal'
        else:
            status = 'dalam rentang normal'
        causes.append(f'{feature_name} = {actual_value:.2f} ({status})')

    return causes


def generate_interpretation(result, probability_map, main_causes, abnormal_count):
    if result == 'Healthy':
        text = (
            f'Model memprediksi pasien ini <strong>SEHAT</strong> dengan probabilitas '
            f'<strong>{probability_map.get("Healthy", 0) * 100:.1f}%</strong>.'
        )
    else:
        text = (
            f'Model memprediksi pasien ini <strong>MENGALAMI ANEMIA</strong> dengan probabilitas '
            f'<strong>{probability_map.get("Anemia", 0) * 100:.1f}%</strong>.'
        )

    if main_causes:
        text += '<br><br><strong>Faktor yang paling memengaruhi prediksi:</strong><br>'
        text += '<br>'.join(f'- {cause}' for cause in main_causes)
        text += '<br><br><strong>Analisis Klinis:</strong><br>'

    if abnormal_count == 0:
        text += (
            'Seluruh parameter darah yang digunakan model berada dalam rentang normal. '
            'Jika prediksi tetap mengarah ke anemia, keputusan tersebut berasal dari pola statistik data training.'
        )
    elif abnormal_count <= 2:
        text += 'Terdapat beberapa parameter di luar rentang normal sehingga dapat memengaruhi hasil prediksi.'
    else:
        text += 'Beberapa parameter darah berada di luar rentang normal dan mendukung hasil prediksi model.'

    if result == 'Healthy':
        text += (
            '<br><br><strong>Interpretasi XAI:</strong><br>'
            'Analisis SHAP dan LIME menunjukkan bahwa parameter darah utama berada pada rentang yang '
            'mendukung kondisi sehat sehingga model mengklasifikasikan pasien sebagai tidak anemia.'
        )
    else:
        text += (
            '<br><br><strong>Interpretasi XAI:</strong><br>'
            'Analisis SHAP dan LIME menunjukkan bahwa fitur-fitur utama memiliki kontribusi terbesar '
            'terhadap keputusan model. Prediksi dibuat berdasarkan pola yang dipelajari dari data training '
            'dan tidak hanya ditentukan oleh batas normal klinis.'
        )

    return text


def generate_summary(shap_summary, lime_summary, result_label):
    if not shap_summary and not lime_summary:
        return 'Tidak ada data interpretasi yang dapat dirangkum.'

    lines = [
        'Analisis Explainable AI (SHAP & LIME) memberikan gambaran tentang faktor darah '
        'yang paling memengaruhi hasil prediksi pasien ini:'
    ]
    feature_desc = {
        'HGB': 'Kadar hemoglobin mencerminkan kemampuan darah membawa oksigen.',
        'HCT': 'Hematokrit menunjukkan proporsi sel darah merah dalam darah.',
        'RBC': 'Jumlah sel darah merah memengaruhi kapasitas oksigen darah.',
        'MCH': 'MCH menunjukkan rata-rata hemoglobin per sel darah merah.',
        'MCHC': 'MCHC menilai konsentrasi hemoglobin di dalam sel darah merah.',
    }

    for feature, shap_value in sorted(shap_summary.items(), key=lambda item: abs(item[1]), reverse=True):
        lime_value = lime_summary.get(feature, 0.0)
        if shap_value > 0 or lime_value > 0:
            direction = 'meningkatkan kemungkinan hasil ini'
        elif shap_value < 0 or lime_value < 0:
            direction = 'menurunkan kemungkinan hasil ini'
        else:
            direction = 'tidak memberikan pengaruh signifikan'
        lines.append(
            f'- <strong>{feature}</strong> {direction} '
            f'(<em>SHAP = {shap_value:+.3f} | LIME = {lime_value:+.3f}</em>). {feature_desc.get(feature, "")}'
        )

    if result_label == 'Healthy':
        lines.append(
            '<br><strong>Kesimpulan Klinis:</strong> '
            'Model memprediksi pasien ini <strong>Sehat (tidak anemia)</strong>. '
            'Nilai HGB dan HCT yang cukup tinggi menjadi faktor dominan yang mendukung hasil ini. '
            'RBC, MCH, dan MCHC juga berada dalam rentang yang mendukung status darah normal. '
            'Interpretasi ini menunjukkan kondisi darah yang efisien dalam membawa oksigen ke seluruh tubuh.'
        )
    else:
        lines.append(
            '<br><strong>Kesimpulan Klinis:</strong> '
            'Model memprediksi pasien ini <strong>mengalami Anemia</strong>. '
            'Nilai HGB dan HCT yang rendah menjadi kontributor utama, '
            'serta dukungan dari penurunan RBC dan MCH yang menunjukkan penurunan kemampuan darah membawa oksigen. '
            'Hasil ini sebaiknya dikonfirmasi dengan pemeriksaan klinis lanjutan.'
        )

    return '<br>'.join(lines)
