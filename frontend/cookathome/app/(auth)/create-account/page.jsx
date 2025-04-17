'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import GlobalApi from '@/app/_Utils/GlobalApi';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

function CreateAccount() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // If the user is already logged in, redirect them to the home page
  useEffect(() => {
    const jwt = sessionStorage.getItem('jwt');
    if (jwt) {
      router.push('/');
    }
  }, [router]);

  const onCreateAccount = async (e) => {
    e.preventDefault();
    setLoading(true);
  
    try {
      const resp = await GlobalApi.registration(username, email, password);
      // Check if the response contains the data we expect
      if (resp.data) {
        console.log('User:', resp.data.user);
        console.log('JWT:', resp.data.jwt);
        sessionStorage.setItem('user', JSON.stringify(resp.data.user));
        sessionStorage.setItem('jwt', resp.data.jwt);
        toast.success('Account created successfully!');
        router.push('/');
      }
    } catch (error) {
      console.error('Registration failed:', error.response?.data || error);
      toast.error('Failed to create an account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center my-20 p-10 bg-slate-100 border border-gray-300 rounded-lg shadow-md max-w-md mx-auto">
     <Image src="/logo.png" alt="Logo" width={200} height={100} priority />

      <h2 className="font-bold text-3xl mb-2">Create an Account</h2>
      <p className="text-gray-600 text-center mb-4">
        Enter your Username, Email, and Password to continue
      </p>

      <form onSubmit={onCreateAccount} className="w-full max-w-sm space-y-3">
        <Input 
          type="text" 
          placeholder="Username" 
          value={username} 
          onChange={(e) => setUsername(e.target.value)} 
          required
        />
        <Input 
          type="email" 
          placeholder="Email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required
        />
        <Input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required
        />

        <Button 
          className="w-full bg-green-600 text-white p-2 rounded-md hover:bg-blue-700 transition disabled:opacity-50"
          type="submit" 
          disabled={!username || !email || !password || loading} 
        >
          {loading ? (
            <div className="flex justify-center items-center">
              <svg
                className="animate-spin h-5 w-5 mr-3 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 12a8 8 0 1 1 16 0 8 8 0 0 1-16 0z"
                />
              </svg>
              Creating Account...
            </div>
          ) : (
            'Create Account'
          )}
        </Button>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        Already have an account? 
        <Link href="/sign-in" className="text-blue-600 hover:underline ml-1">
          Click here to Sign In
        </Link>
      </p>
    </div>
  );
}

export default CreateAccount;
