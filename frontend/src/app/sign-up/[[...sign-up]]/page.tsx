import { SignUp } from "@clerk/nextjs";
export default function Page(){return <main className="grid min-h-screen place-items-center bg-[#0b1018]"><SignUp routing="path" path="/sign-up" signInUrl="/sign-in"/></main>;}
