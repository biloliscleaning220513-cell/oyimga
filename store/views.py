from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Product, Review
from .forms import ReviewForm

def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            try:
                review.full_clean()
                review.save()
                messages.success(request, "Fikringiz muvaffaqiyatli saqlandi!")
                return redirect('product_detail', pk=product.pk)
            except Exception as e:
                for error in e.messages if hasattr(e, 'messages') else [str(e)]:
                    messages.error(request, error)
        else:
            messages.error(request, "Iltimos, forma ma'lumotlarini to'g'ri to'ldiring.")
    else:
        form = ReviewForm()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form
    })
