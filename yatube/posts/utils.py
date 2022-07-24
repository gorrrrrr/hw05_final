from django.core.paginator import Paginator

from yatube.settings import POST_NUMBER


def paginate(obj, request):
    """Нарезает длинную последоваельность постов на страницы."""
    paginator = Paginator(obj, POST_NUMBER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
