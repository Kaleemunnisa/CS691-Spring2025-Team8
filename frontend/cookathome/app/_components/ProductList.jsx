import React from "react";
import ProductItem from "./ProductItem";

function ProductList({ products = [] }) {
  console.log("Received Products:", products); // Debugging

  return (
    <div className="mt-10">
      <h2 className="text-green-600 font-bold text-2xl mb-4 text-left">
        Our Popular Products
      </h2>
      {Array.isArray(products) && products.length === 0 ? (
        <p className="text-center text-gray-500">No products available</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5 mt-6">
          {Array.isArray(products) ? (
            products.map((product) => (
              <ProductItem key={product.id} product={product} />
            ))
          ) : (
            <p className="text-center text-red-500">Error: Invalid product data</p>
          )}
        </div>
      )}
    </div>
  );
}

export default ProductList;
