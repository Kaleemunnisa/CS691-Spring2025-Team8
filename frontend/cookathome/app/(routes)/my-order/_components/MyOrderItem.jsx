import Image from 'next/image';
import React from 'react';

function MyOrderItem({ orderItem }) {
  const product = orderItem?.product?.data || {};
  const productName = product?.name || 'Unnamed Product';
  const productImage = product?.images?.data?.[0]?.url || '/placeholder.png';
  
  // Prefer product mrp, else fallback to orderItem.price
  const productMrp = Number(product?.mrp) || Number(orderItem?.price) || 0;

  const formattedPrice = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(productMrp);

  const formattedAmount = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(orderItem.amount || orderItem.price || 0);

  const imageAltText = productName || 'Product image';

  return (
    <div className='w-full'>
      <div className='grid grid-cols-5 gap-4 mt-4 items-center'>
        <Image
          src={productImage}
          width={80}
          height={80}
          alt={imageAltText}
          className='bg-gray-100 p-2 rounded-md border object-contain'
        />
        <div className='col-span-2'>
          <h2 className='font-semibold'>{productName}</h2>
          <p className='text-sm text-gray-600'>
            Item Price: {formattedPrice || 'Price not available'}
          </p>
        </div>
        <p className='text-sm'>Quantity: {orderItem.quantity || 'N/A'}</p>
        <p className='text-sm'>Total: {formattedAmount || '₹0.00'}</p>
      </div>
      <hr className='mt-3' />
    </div>
  );
}

export default MyOrderItem;
