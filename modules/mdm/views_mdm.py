
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponse
from django.views.generic import TemplateView
from modules.mdm.models import (
    TableSetting,
)
from datetime import datetime
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import ExcelUploadForm
import pandas as pd
from django.contrib import messages
import os
from django.conf import settings



def index(request):
    return HttpResponse("Master Referensi")

class PreviewMdmView(LoginRequiredMixin, TemplateView):
    template_name = "mdm/preview_table_list.html"

    def get_context_data(self, **kwargs):
        with connections['mdm'].cursor() as cursor:
            # Get the list of table names using the cursor's connection
            cursor.execute("SELECT nama, uraian_table FROM public.table_setting WHERE status=true")
            # cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            list_data = cursor.fetchall()
        context = super().get_context_data(**kwargs)
        context["list_data"] = list_data
        context["title"] = 'Master Referensi'
        return context

class PreviewMdmRecordsView(LoginRequiredMixin, TemplateView):
    template_name = "mdm/preview_table_records.html"

    def get_context_data(self, mdm_table_name, **kwargs):
        context = super().get_context_data(**kwargs)
        with connections['mdm'].cursor() as cursor:
            cursor.execute("SELECT list_data, uraian_table FROM public.table_setting as t WHERE t.nama=%s", (mdm_table_name,))
            list_data = cursor.fetchall()

        with connections['mdm'].cursor() as cursor2:
            query = f"SELECT {list_data[0][0]} FROM {mdm_table_name}"
            cursor2.execute(query)
            columns = [col[0] for col in cursor2.description]
            records = cursor2.fetchall()

        excel_upload_form = ExcelUploadForm()  # Add this line

        context = {
            'title': 'Master Data - ' + list_data[0][1],
            'table_name': mdm_table_name,
            'columns': columns,
            'records': records,
            'excel_upload_form': excel_upload_form,  # Add this line
        }
        return context

    def post(self, request, mdm_table_name, **kwargs):            
        excel_upload_form = ExcelUploadForm(request.POST, request.FILES)

        with connections['mdm'].cursor() as cursor:
            cursor.execute("SELECT list_data, uraian_table FROM public.table_setting as t WHERE t.nama=%s", (mdm_table_name,))
            list_data = cursor.fetchall()
        with connections['mdm'].cursor() as cursor2:
            query = f"SELECT {list_data[0][0]} FROM {mdm_table_name}"
            cursor2.execute(query)
            columns = [col[0] for col in cursor2.description]
            records = cursor2.fetchall()

        if excel_upload_form.is_valid():
            # Get the uploaded file
            excel_file = request.FILES['excel_file']

            # Read Excel data using pandas
            df = pd.read_excel(excel_file)

            # Insert data into the database table using a query
            with connections['mdm'].cursor() as cursor:
                values_list = []

                if mdm_table_name == 'keu_tags':
                    for row in df.itertuples(index=False, name=None):
                        formatted_values = ', '.join([f"'{value}'" if isinstance(value, str) else str(value) for value in row])
                        values_list.append(f'({formatted_values})')

                    # Join the list of values to create the VALUES part of the query
                    values = ', '.join(values_list)

                    # Define the update part of the query
                    update_clause = ', '.join([f"{column} = EXCLUDED.{column}" for column in columns])

                    # Construct the upsert query using ON CONFLICT
                    query = f"INSERT INTO {mdm_table_name} VALUES {values} ON CONFLICT (id) DO UPDATE SET {update_clause};"
                    cursor.execute(query)
                elif mdm_table_name =='vw_keu_kegiatan_mapping':
                    mdm_table_name_store = 'keu_kegiatan_mapping_temp'
                    values_list = []

                    for row in df.itertuples(index=False, name=None):
                        formatted_values = ', '.join([f"'{str(value).zfill(2)}'" if value is not None and value == value else "''" for value in row])
                        values_list.append(f'({formatted_values})')

                    # Join the list of values to create the VALUES part of the query
                    values = ', '.join(values_list)

                    with connections['mdm'].cursor() as cursor2_kegiatan:
                        query_kegiatan = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{mdm_table_name_store}'"
                        cursor2_kegiatan.execute(query_kegiatan)
                        columns_kegiatan = [row[0] for row in cursor2_kegiatan.fetchall()]

                    # Define the update part of the query
                    update_clause = ', '.join([f"{column} = EXCLUDED.{column}" for column in columns_kegiatan])

                    # Construct the upsert query using ON CONFLICT
                    query = f"INSERT INTO {mdm_table_name_store} VALUES {values} ON CONFLICT (tahun, kodesubkegiatan, tags) DO UPDATE SET {update_clause};"

                    cursor.execute(query)
                    cursor.execute("SELECT mapping_kegiatan_temp_to_kegiatan();")

            with connections['mdm'].cursor() as cursor2:
                query = f"SELECT {list_data[0][0]} FROM {mdm_table_name} ORDER BY updated_at DESC;"
                cursor2.execute(query)
                columns = [col[0] for col in cursor2.description]
                records = cursor2.fetchall()

            messages.success(request,"Data Berhasil di Simpan !!")
            return render(
                request,
                self.template_name,
                {
                    'title': 'Master Data - ' + mdm_table_name,
                    'table_name': mdm_table_name,
                    'columns': columns,
                    'records': records,
                    'excel_upload_form': excel_upload_form,
                },
            )

        return render(
            request,
            self.template_name,
            {
                'title': 'Master Data - ' + mdm_table_name,
                'table_name': mdm_table_name,
                'columns': columns,
                'records': records,
                'excel_upload_form': excel_upload_form,
            },
        )

def get_table_list(request, mdm_table_name):
    with connections['mdm'].cursor() as cursor:
        # Dynamically construct the SQL query
        query = f"SELECT * FROM {mdm_table_name};"
        cursor.execute(query)

        # Fetch all the rows from the result set
        rows = cursor.fetchall()

    # Convert the rows to a list of dictionaries
    data = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
    return JsonResponse(data, safe=False)

def download_template(request, mdm_table_name):
    table = ''
    if mdm_table_name == 'keu_tags':
        table = 'tag'
    elif mdm_table_name == 'vw_keu_kegiatan_mapping':
        table = 'kegiatan'

    base_dir = settings.BASE_DIR
    template_filename = f'template_{table}.xlsx'
    template_path = os.path.join(base_dir, 'modules', 'mdm', 'templates', template_filename)

    with open(template_path, 'rb') as template_file:
        response = HttpResponse(template_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={template_filename}'
        return response

class PreviewMdmAPIView(LoginRequiredMixin, TemplateView):
    template_name = "mdm/preview_api_table_list.html"

    def get_context_data(self, **kwargs):
        with connections['mdm'].cursor() as cursor:
            # Get the list of table names using the cursor's connection
            cursor.execute("SELECT nama, uraian_table FROM public.table_setting WHERE status=true")
            # cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            list_data = cursor.fetchall()
        context = super().get_context_data(**kwargs)
        context["list_data"] = list_data
        context["title"] = 'Master Referensi API'
        return context