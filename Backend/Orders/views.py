from django.shortcuts import get_object_or_404
from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services import send_sms

from .models import Order
from .serializers import OrderSerializer


class OrderAPIView(APIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, TokenHasScope]
    required_scopes = ["openid"]

    def post(self, request):
        """POST request function to create a new Order object."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # 1. Save the instance to the database
            order = serializer.save()

            # 2. Extract values from saved instance or validated_data
            customer = (
                order.customer
            )  # Assuming Order model has a foreign key to Customer

            # Format customer full name with a space
            full_name = f"{customer.first_name} {customer.last_name}"

            # 3. Send SMS notification using computed order properties/data
            send_sms(
                full_name,
                serializer.data.get("item_name", getattr(order.item, "name", "")),
                order.quantity,
                serializer.data["total"],  # Available now after serializer.save()
                customer.phone_number,
            )

            return Response(
                {
                    "status": status.HTTP_201_CREATED,
                    "message": (
                        "Order Created Successfully! An SMS has been "
                        "sent to the customer for delivery"
                    ),
                    "results": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "An Error Occurred!",
                "results": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get(self, request, pk=None):
        ("""GET request function to retrieve a single Order or"
            "list all Orders.""")
        if pk:
            try:
                order_obj = get_object_or_404(Order, id=pk)
                serializer = self.serializer_class(order_obj)
                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Order Details Retrieved Successfully!",
                        "results": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "An Error Occurred!",
                        "results": {"error": str(e)},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Standard list retrieval does not require a try/except block
        order_objs = Order.objects.all().order_by("-date_created")
        serializer = self.serializer_class(
            order_objs, many=True, context={"request": request}
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "message": "Orders Retrieved Successfully!",
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk=None):
        """PATCH request function to update a given Order object."""
        try:
            order_obj = get_object_or_404(Order, id=pk)
            serializer = self.serializer_class(
                instance=order_obj, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Order Details Updated Successfully!",
                        "results": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": {"error": str(e)},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, pk=None):
        """DELETE request function to delete a given Order object."""
        try:
            order_obj = get_object_or_404(Order, id=pk)
            order_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "An Error Occurred!",
                    "results": {"error": str(e)},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
