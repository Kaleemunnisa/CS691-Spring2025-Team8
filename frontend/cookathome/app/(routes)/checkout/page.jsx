"use client";
import GlobalApi from '@/app/_Utils/GlobalApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PayPalButtons } from '@paypal/react-paypal-js';
import { ArrowBigRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';

function Checkout() {
  const user = JSON.parse(sessionStorage.getItem('user'));
  const jwt = sessionStorage.getItem('jwt');
  const [totalCartItem, setTotalCartItem] = useState(0);
  const [cartItemList, setCartItemList] = useState([]);
  const [subtotal, setSubTotal] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [zip, setZip] = useState('');
  const [address, setAddress] = useState('');

  const router = useRouter();

  useEffect(() => {
    if (!jwt) {
      router.push('/sign-in');
    }
    getCartItems();
  }, []);

  // Fetch Cart Items
  const getCartItems = async () => {
    try {
      const cartItemList_ = await GlobalApi.getCartItems(user.id, jwt);
      setTotalCartItem(cartItemList_?.length || 0);
      setCartItemList(cartItemList_);
    } catch (error) {
      console.error('Error fetching cart items:', error);
      setTotalCartItem(0);
      setCartItemList([]);
    }
  };

  // Calculate the totals based on cart items
  useEffect(() => {
    let total = 0;
    cartItemList.forEach((item) => {
      total += item.amount;
    });
    setSubTotal(total.toFixed(2));
    setTotalAmount((total * 0.9 + 15).toFixed(2)); // 9% tax + $15 delivery
  }, [cartItemList]);

  // Total amount calculation function
  const calculateTotalAmount = () => {
    return (subtotal * 0.09 + 15 + parseFloat(subtotal)).toFixed(2); // 9% tax + $15 delivery
  };

  const onApprove = async (data, actions) => {
    try {
      if (!username || !email || !phone || !zip || !address) {
        toast.error('Please fill all billing details');
        return;
      }

      const paymentId = data.orderID || '123'; // Payment ID comes from PayPal data or hardcoded '123' for testing
      if (!paymentId) {
        toast.error('Missing payment ID');
        return;
      }

      const payload = {
        data: {
          totalOrderAmount: Math.round(totalAmount * 100),
          username,
          email,
          phone,
          zip,
          address,
          orderItemList: cartItemList.map((item) => ({
            name:item.name,
            product: item.productId,
            quantity: item.quantity,
            price: item.amount,
          })),
          userId: user.id,
          paymentId: paymentId, // Send the payment ID in the payload
        }
      };

      console.log('Sending payload:', JSON.stringify(payload, null, 2));

      const response = await GlobalApi.createOrder(payload, jwt);
      console.log('Order created:', response);

      await Promise.all(
        cartItemList.map((item) => GlobalApi.deleteCartItem(item.cartId, jwt))
      );

      toast.success('Order Placed Successfully!');
      router.replace('/order-confirmation');
    } catch (error) {
      console.error('Order creation failed:', error?.response?.data || error.message);
      toast.error('Order failed. Please try again.');
    }
  };

  return (
    <div className="checkout-container">
      <h2 className="p-3 bg-primary text-xl font-bold text-center text-white">Checkout</h2>
      <div className="p-5 px-5 md:px-10 grid grid-cols-1 md:grid-cols-3 py-8">
        <div className="md:col-span-2 mx-20">
          <h2 className="font-bold text-3xl">Billing Details</h2>
          <div className="grid grid-cols-2 gap-10 mt-3">
            <Input placeholder="Name" onChange={(e) => setUsername(e.target.value)} />
            <Input placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-10 mt-3">
            <Input placeholder="Phone" onChange={(e) => setPhone(e.target.value)} />
            <Input placeholder="Zip" onChange={(e) => setZip(e.target.value)} />
          </div>
          <div className="mt-3">
            <Input placeholder="Address" onChange={(e) => setAddress(e.target.value)} />
          </div>
        </div>

        <div className="mx-10 border rounded-lg shadow-sm p-4">
          <h2 className="p-3 bg-gray-200 font-bold text-center">Total Cart ({totalCartItem})</h2>
          <div className="p-4 flex flex-col gap-4">
            <h2 className="font-bold flex justify-between">
              Subtotal: <span>${subtotal}</span>
            </h2>
            <hr />
            <h2 className="flex justify-between">
              Delivery: <span>$15.00</span>
            </h2>
            <h2 className="flex justify-between">
              Tax (9%): <span>${(subtotal * 0.09).toFixed(2)}</span>
            </h2>
            <hr />
            <h2 className="font-bold flex justify-between">
              Total: <span>${calculateTotalAmount()}</span>
            </h2>

            <Button onClick={() => onApprove({ paymentId: '123' })}>
              Test Payment <ArrowBigRight />
            </Button>

            {totalAmount > 15 && (
              <PayPalButtons
                disabled={!(username && email && address && zip)}
                style={{ layout: 'horizontal' }}
                onApprove={onApprove}
                createOrder={(data, actions) => {
                  return actions.order.create({
                    purchase_units: [
                      {
                        amount: {
                          value: totalAmount,
                          currency_code: 'USD',
                        },
                      },
                    ],
                  });
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Checkout;
