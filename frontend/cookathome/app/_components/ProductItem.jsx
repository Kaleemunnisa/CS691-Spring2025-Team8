import React from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";

function ProductItem({ product }) {
  

  return (
    <div className="p-2 md:p-6 flex flex-col items-center justify-center gap-3 border rounded-lg hover:scale-110 hover:shadow-md transition-all ease-in-out">
      {/* Product Image */}
      {product.images?.length > 0 && (
        <Image
          src={process.env.NEXT_PUBLIC_BACKEND_BASE_URL + product.images[0].url}
          alt={product.name}
          width={200}
          height={200}
          className="h-[200px] w-[200px]"
        />
      )}

      {/* Product Details */}
      <h2 className="text-lg font-semibold">{product.name}</h2>

      {/* Show Selling Price & MRP Differently */}
      <div className="flex items-center gap-2">
        {product.SellingPrice ? (
          <>
            <h2 className="text-red-600 text-lg font-bold">${product.SellingPrice}</h2>
            <h2 className="text-gray-500 line-through">${product.mrp}</h2>
          </>
        ) : (
          <h2 className="text-gray-800 text-lg">${product.mrp}</h2>
        )}
      </div>

      {/* Add to Cart Button */}
      <Button variant="outline" className="text-primary hover:bg-primary">
        Add to cart
      </Button>
    </div>
  );
}

export default ProductItem;
