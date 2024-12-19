from django.shortcuts import render
from .serializers import BookSerializer, UserSerializer, TransactionSerializer
from .models import Book, User,Transactions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from rest_framework.decorators import action
from  rest_framework import filters
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
class BookPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BookView(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['Title', 'Author', 'ISBN']
    ordering_fields = ['Title', 'Author', 'ISBN']
    ordering = ['Title']
    authentication_classes = [TokenAuthentication]
    pagination_class = BookPagination
    


    def get_queryset(self):
        queryset = super().get_queryset()
        available = self.request.query_params.get('available', None)
        if available is not None:
            if available.lower() == 'true':
                queryset = queryset.filter(Number_of_copies_Available__gt=0)
            elif available.lower() == 'false':
                queryset = queryset.filter(Number_of_copies_Available__lte=0)
        return queryset
class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class BookCheckoutView(viewsets.ModelViewSet):
    queryset = Transactions.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def create(self, request, *args, **kwargs):
        user = request.user
        book_id = request.data.get('book')
        book = Book.objects.get(id=book_id)

        if book.Number_of_copies_Available < 1:
            return Response({"error": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)

        if TransactionSerializer.objects.filter(user=user, book=book).exists():
            return Response({"error": "You have already checked out this book"}, status=status.HTTP_400_BAD_REQUEST)

        book.Number_of_copies_Available -= 1
        book.save()

        checkout = TransactionSerializer.objects.create(user=user, book=book)
        serializer = self.get_serializer(checkout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='return')
    def return_book(self, request):
        user = request.user
        book_id = request.data.get('book')
        book = Book.objects.get(id=book_id)

        checkout = Transactions.objects.filter(user=user, book=book, return_date__isnull=True).first()
        
        if not checkout:
            return Response({"error": "You have not checked out this book"}, status=status.HTTP_400_BAD_REQUEST)

        checkout.return_date = timezone.now().date()
        
        if checkout.return_date > checkout.due_date:
            overdue_days = (checkout.return_date - checkout.due_date).days
            checkout.penalty = overdue_days * 1.00  # Example penalty calculation
            send_mail(
                'Overdue Book Return',
                f'Dear {user.username}, you have returned the book "{book.Title}" {overdue_days} days late. Your penalty is ${checkout.penalty}.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        checkout.save()


        book.Number_of_copies_Available += 1
        book.save()

        serializer = self.get_serializer(checkout)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserBorrowingHistoryView(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='borrowing-history')
    def borrowing_history(self, request):
        user = request.user
        borrowings = Transactions.objects.filter(user=user)
        serializer = TransactionSerializer(borrowings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    