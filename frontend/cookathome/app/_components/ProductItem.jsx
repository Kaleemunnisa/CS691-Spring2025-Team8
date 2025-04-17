import React from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import ProductItemDetail from "./ProductItemDetail"; // ✅ Import ProductItemDetail

function ProductItem({ product }) {
  return (
    <div className="p-2 md:p-6 flex flex-col items-center justify-center gap-3 border rounded-lg hover:scale-105 hover:shadow-md transition-all ease-in-out">
      {/* Product Image */}
      {product.image?.length > 0 && (
        <Image
          src={`${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}${product.image[0].url}`}
          alt={product.name}
          width={200}
          height={200}
          className="h-[200px] w-[200px] object-contain"
        />
      )}

      {/* Product Details */}
      <h2 className="text-lg font-semibold text-center">{product.name}</h2>

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

      {/* Add to Cart Button with Dialog */}
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="outline" className="text-primary border-primary hover:bg-primary hover:text-white">
            Add to Cart
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Product Details</DialogTitle>
          </DialogHeader>
          
          <ProductItemDetail product={product} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ProductItem;