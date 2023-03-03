from django.core.paginator import Paginator


POST_NUMBER = 10


def pagination(request, posts):
    paginator = Paginator(posts, POST_NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
