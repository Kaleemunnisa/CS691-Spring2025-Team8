"use client"
import { Button } from '@/components/ui/button';
import { CircleUserRound, LayoutGrid, Search, ShoppingBasket } from 'lucide-react';
import Image from 'next/image';
import React, { useContext, useEffect, useState } from 'react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import GlobalApi from '../_Utils/GlobalApi';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { UpdateCartContext } from '../_context/UpdateCartContext';
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetDescription,SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import CartItemList from './CartItemList';
import { toast } from 'sonner';


function Header() {
    const [categoryList, setCategoryList] = useState([]);
    const isLogin = sessionStorage.getItem('jwt') ? true : false;
    const user = JSON.parse(sessionStorage.getItem('user'));
    const jwt = sessionStorage.getItem('jwt');
    const [totalCartItem, setTotalCartItem] = useState(0);
    const { updateCart, setUpdateCart } = useContext(UpdateCartContext);
    const [cartItemList, setCartItemList] = useState([]);
    const router = useRouter();

    useEffect(() => {
        getCategoryList();
    }, []);

    useEffect(() => {
        getCartItems();
    }, [updateCart]);
    const getCategoryList=()=>{
        GlobalApi.getCategory().then(resp=>{
            setCategoryList(resp.data.data);
        })
    }


   
    const [errorMessage, setErrorMessage] = useState('');

    const getCartItems = async () => {
      if (user && user.id) {
        try {
          const cartItemList_ = await GlobalApi.getCartItems(user.id, jwt);
          console.log(cartItemList_);
          setTotalCartItem(cartItemList_?.length);
          setCartItemList(cartItemList_);
          setErrorMessage(''); // Clear previous errors
        } catch (error) {
          setErrorMessage("Failed to fetch cart items. Please try again.");
        }
      } else {
        setErrorMessage("User is not logged in or user ID is missing.");
      }
    };
    
      
    


    const onSignOut = () => {
        sessionStorage.clear();
        router.push('/sign-in');
    };

  
    const onDeleteItem = (id) => {
        GlobalApi.deleteCartItem(id, jwt).then(resp => {
          toast('Item removed!');
        }).catch(error => {
          toast.error('Failed to remove item');
          console.error(error);
        });
      }

    const [subtotal, setSubTotal] = useState(0);

    useEffect(() => {
        let total = 0;
        cartItemList.forEach(element => {
            total = total + element.amount;
        });
        setSubTotal(total.toFixed(2));
    }, [cartItemList]);

    return (
        <div className='p-5 shadow-sm flex justify-between'>
            <div className='flex items-center gap-8'>
                <Link href={'/'}>
                    <Image src='/logo.png' alt='logo' width={150} height={100} className='cursor-pointer' />
                </Link>

                {/* Category Dropdown */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <h2 className='hidden md:flex gap-2 items-center border rounded-full p-2 px-10 bg-slate-200 cursor-pointer'>
                            <LayoutGrid className='h-5 w-5' /> Category
                        </h2>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                        <DropdownMenuLabel>Browse Category</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {categoryList.length === 0 ? (
                            <DropdownMenuItem>Loading categories...</DropdownMenuItem>
                        ) : (
                            categoryList.map((category, index) => {
                                const iconUrl = category?.icon?.[0]?.url
                                    ? `${process.env.NEXT_PUBLIC_BACKEND_BASE_URL}${category.icon[0].url}`
                                    : null;
                                const categoryName = category?.name || "Unknown";
                                return (
                                    <DropdownMenuItem key={index} className="flex items-center gap-2 cursor-pointer">
                                        {iconUrl ? (
                                            <Image src={iconUrl} alt="icon" width={30} height={27} />
                                        ) : (
                                            <span>🖼️</span>
                                        )}
                                        <h2 className="text-lg">{categoryName}</h2>
                                    </DropdownMenuItem>
                                );
                            })
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>

                <div className='md:flex gap-3 items-center border rounded-full p-2 px-5 hidden'>
                    <Search />
                    <input type="text" placeholder='Search' className='outline-none' />
                </div>
            </div>

            {/* Cart and User Login */}
            <div className='flex gap-5 items-center'>
                <Sheet>
                    <SheetTrigger>
                        <h2 className='flex gap-2 items-center text-lg'>
                            <ShoppingBasket className='h-7 w-7' />
                            <span className='bg-primary text-white px-2 rounded-full'>{totalCartItem}</span>
                        </h2>
                    </SheetTrigger>
                    <SheetContent>
                        <SheetHeader>
                            <SheetTitle className="bg-primary text-white font-bold text-lg p-2">My Cart</SheetTitle>
                            <SheetDescription>
                            <CartItemList cartItemList={cartItemList} 
                   onDeleteItem={onDeleteItem}/>
                            </SheetDescription>
                        </SheetHeader>
                        <SheetClose asChild>
                            <div className='absolute w-[90%] bottom-6 flex flex-col'>
                                <h2 className='text-lg font-bold flex justify-between'>
                                    Subtotal <span>${subtotal}</span>
                                </h2>
                                <Button 
                    disabled={cartItemList.length==0}
                    onClick={()=>router.push(jwt?'/checkout':'/sign-in')}>Checkout</Button>
</div>
                </SheetClose>
            </SheetContent>
            </Sheet>

            {!isLogin?  <Link href={'/sign-in'}>
                <Button>Login</Button>
            </Link>
            :
            <DropdownMenu>
  <DropdownMenuTrigger asChild>
  <CircleUserRound 
            className="bg-green-100
            p-2 rounded-full cursor-pointer
             text-primary h-12 w-12"
            />   
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>My Account</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem>Profile</DropdownMenuItem>
   <Link href={'/my-order'}>
     <DropdownMenuItem>My Order</DropdownMenuItem>
     </Link>
   
    <DropdownMenuItem onClick={()=>onSignOut()}>Logout</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
 
        }
        </div>
    </div>
  )
}

export default Header
