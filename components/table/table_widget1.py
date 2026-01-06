from django_components import component
import json

@component.register("table_widget1")
class TableWidget1(component.Component):
    template_name = "table/table_widget1.html"
    
    def get_context_data(self, tables):
        # Expect data is [ {"id": 1, "name": "Andi", "age": 20} ]
        # then header is [ "id", "name", "age"]
        # and content is [ [1, "Andi", 20] ]

        # print(f"\n\n data====================> {tables}\n\n")
        if isinstance(tables, str):
            try:
                tables = json.loads(tables)
            except json.JSONDecodeError:
                tables = []
        return {
            "header": list(tables[0].keys()),
            "contents": [list(tr.values()) for tr in tables],
        }