import Image from "next/image";
import { TrashIcon } from "lucide-react";
import React from "react";

function CartItemList({ cartItemList, onDeleteItem }) {
  return (
    <div className="h-[500px] overflow-auto space-y-4">
      {cartItemList.length === 0 ? (
        <div className="text-center text-gray-500 py-8">Your cart is empty.</div>
      ) : (
        cartItemList.map((cart, index) => (
          <div
            key={cart.id || index}
            className="flex justify-between items-center p-4 border rounded-md shadow-sm"
          >
            <div className="flex gap-6 items-center">
              {cart.productImage ? (
                <Image
                  src={cart.productImage}
                  width={70}
                  height={70}
                  alt={cart.productName || "Product Image"}
                  className="rounded-md object-cover aspect-square border"
                />
              ) : (
                <div className="w-16 h-16 bg-gray-200 flex items-center justify-center text-gray-600 rounded-md border">
                  No Image
                </div>
              )}
                <div>
                        <h2 className='font-bold'>{cart.productName}</h2>
                        <h2 className=''>Quantity {cart.quantity}</h2>
                        <h2 className='text-lg font-bold'>$ {cart.amount}</h2>
                    </div>
             
            </div>
.
  
  <TrashIcon
    className="w-5 h-5 text-gray-500 hover:text-red-600 cursor-pointer transition"
    onClick={() => onDeleteItem(cart.id)}  // Make sure this matches your data structure
    aria-label="Remove item from cart"
  />
  
 

          </div>
        ))
      )}
    </div>
  );
}

export default CartItemList;
