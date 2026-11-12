import { SignIn } from "@clerk/nextjs";
export default function Page(){return <main className="grid min-h-screen place-items-center bg-[#0b1018]"><SignIn routing="path" path="/sign-in" signUpUrl="/sign-up"/></main>;}
