import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
const API = process.env.DEVSTATE_API_URL;
async function proxy(req:NextRequest,ctx:{params:Promise<{path:string[]}>}) {
 if(!API) return NextResponse.json({detail:"Backend not configured"},{status:503});
 const {userId,getToken}=await auth();
 if(!userId) return NextResponse.json({detail:"Authentication required"},{status:401});
 const token=await getToken();
 if(!token) return NextResponse.json({detail:"Clerk session token unavailable"},{status:401});
 const {path}=await ctx.params;
 const target=new URL(path.map(encodeURIComponent).join("/") + req.nextUrl.search,API.endsWith("/")?API:API+"/");
 const headers=new Headers({Authorization:"Bearer "+token});
 const ct=req.headers.get("content-type"); if(ct) headers.set("Content-Type",ct);
 const body=["GET","HEAD"].includes(req.method)?undefined:await req.arrayBuffer();
 try { const upstream=await fetch(target,{method:req.method,headers,body,cache:"no-store",redirect:"manual"});
 return new NextResponse(upstream.body,{status:upstream.status,headers:{"Content-Type":upstream.headers.get("content-type")||"application/json"}}); }
 catch { return NextResponse.json({detail:"Backend unavailable"},{status:502}); }
}
export const GET=proxy; export const POST=proxy; export const PATCH=proxy; export const PUT=proxy; export const DELETE=proxy;
