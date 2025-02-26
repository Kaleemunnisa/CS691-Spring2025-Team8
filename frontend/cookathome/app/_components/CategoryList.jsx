import React from "react";
import Image from "next/image";

function CategoryList({ categoryList }) {
  return (
    <div className="mt-5 w-full">
      <h2 className="text-green-600 font-bold text-2xl mb-4 text-left">
        Shop by Category
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 m lg:grid-cols-4 gap-5 mt-6">
        {categoryList.map((category) => {
          const iconUrl = category?.attributes?.icon?.[0]?.url
            ? `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}${category.attributes.icon[0].url}`
            : null;

          return (
            <div 
              key={category.id} 
              className="flex flex-col items-center bg-green-50 gap-2 p-4 rounded-lg group cursor-pointer transition-transform hover:scale-105"
            >
              {iconUrl ? (
                <Image
                  src={iconUrl}
                  width={80}
                  height={80}
                  alt={category.attributes.name}
                  className="group-hover:scale-110 transition-all"
                />
              ) : (
                <div className="w-[80px] h-[80px] bg-gray-200 rounded-full flex items-center justify-center">
                  No Image
                </div>
              )}
              <p className="text-lg font-semibold mt-2 text-center">{category.attributes.name}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default CategoryList;
