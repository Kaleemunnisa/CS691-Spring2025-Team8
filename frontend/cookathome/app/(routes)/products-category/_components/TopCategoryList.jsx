import React from 'react';
import Link from "next/link";
import Image from "next/image";

function TopCategoryList({ categoryList = [] }) {  // Ensure default array
  if (!Array.isArray(categoryList)) {
    console.error("categoryList is not an array:", categoryList);
    return <p className="text-center text-red-500">No categories available.</p>;
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-5 mt-6">
      {categoryList.map((category) => {
        const iconUrl = category?.icon?.[0]?.url
          ? `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}${category.icon[0].url}`
          : null;

        const categorySlug = category.name.toLowerCase().replace(/\s+/g, "-");

        return (
          <Link key={category.id} href={`/products-category/${categorySlug}`}>
            <div className="flex flex-col items-center bg-green-50 gap-2 p-4 rounded-lg group cursor-pointer transition-transform hover:scale-105">
              {iconUrl ? (
                <Image
                  src={iconUrl}
                  width={80}
                  height={80}
                  alt={category.name}
                  className="group-hover:scale-110 transition-all"
                />
              ) : (
                <div className="w-[80px] h-[80px] bg-gray-200 rounded-full flex items-center justify-center">
                  No Image
                </div>
              )}
              <p className="text-lg font-semibold mt-2 text-center">
                {category.name}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

export default TopCategoryList;
