import json

from django.shortcuts import render

from .samples import SAMPLES, build_sql


def inbox(request):
    return render(request, "documents/inbox.html")


def review(request):
    key = request.GET.get("doc", "invoice")
    doc = SAMPLES.get(key, SAMPLES["invoice"])
    payload = json.dumps(doc["payload"], indent=2)
    sql = build_sql(doc["table"], doc["payload"])
    return render(
        request,
        "documents/review.html",
        {"doc": doc, "payload": payload, "sql": sql},
    )


def exceptions(request):
    return render(request, "documents/exceptions.html")
