from django.shortcuts import render


def schemas(request):
    return render(request, "schemas/schemas.html")
