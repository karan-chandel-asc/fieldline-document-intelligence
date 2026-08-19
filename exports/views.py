import json

from django.shortcuts import render

from documents.samples import INVOICE_JSON, build_sql


def exports(request):
    sample = json.dumps(INVOICE_JSON, indent=2)
    sql = build_sql("invoice_extract", INVOICE_JSON)
    return render(
        request,
        "exports/exports.html",
        {"sample_json": sample, "sql": sql},
    )
