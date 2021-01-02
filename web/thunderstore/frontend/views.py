from django.shortcuts import render


def handle404(request, exception):
    return render(request, "errors/404.html", locals())


def handle500(request):
    return render(request, "errors/500.html", locals())


def ads_txt_view(request):
    return render(request, "ads.txt", locals())


def robots_txt_view(request):
    return render(request, "robots.txt", locals())
