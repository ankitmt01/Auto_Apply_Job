
import React, {useState} from 'react';
export const Select: React.FC<{children:any}> = ({children}) => <div className="relative">{children}</div>;
export const SelectTrigger: React.FC<React.HTMLAttributes<HTMLButtonElement>> = ({children}) => <button className="w-full rounded-xl border px-3 py-2 text-left text-sm">{children}</button>;
export const SelectContent: React.FC<{children:any}> = ({children}) => <div className="mt-1 rounded-xl border bg-white p-2 text-sm">{children}</div>;
export const SelectItem: React.FC<{value:string}> = ({children}) => <div className="cursor-pointer rounded-lg px-2 py-1 hover:bg-zinc-100">{children}</div>;
export const SelectValue: React.FC<{placeholder?:string}> = ({placeholder}) => <span className="text-zinc-500">{placeholder}</span>;
