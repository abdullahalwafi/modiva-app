from django_components import component
import json

def transform(data):
    if not data:
        return [], []
    # Extract the keys from the first dictionary in the data
    header = list(data[0].keys())
    # Initialize an empty list for the content
    content = []
    for item in data:
        # Create a list of values for each key in the same order as the header
        row = [item[key] for key in header]
        content.append(row)
    return header, content

@component.register("table")
class Table(component.Component):
    template_name = "table/table.html"

    def get_context_data(self, data):
        # Expect data is [ {"id": 1, "name": "Andi", "age": 20} ]
        # then header is [ "id", "name", "age"]
        # and content is [ [1, "Andi", 20] ]

        # header, content = transform(data)
        # return {
        #     "header": header,
        #     "content": content
        # }
        tbody = data[1]
        if isinstance(data[1], str):
            try:
                tbody = json.loads(tbody)
            except json.JSONDecodeError:
                tbody = []
        return {
            "header": data[0],
            "contents": tbody
        }