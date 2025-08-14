
import React, { useState, createContext, useContext } from 'react';
const TabsCtx = createContext({value:'', setValue: (v:string)=>{}} as any);
export const Tabs: React.FC<{value:string, onValueChange:(v:string)=>void, children:any}> = ({value, onValueChange, children}) => (
  <TabsCtx.Provider value={{value, setValue:onValueChange}}>{children}</TabsCtx.Provider>
);
export const TabsList: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({className='', ...props}) => (
  <div className={['inline-flex gap-1 rounded-xl border bg-white p-1', className].join(' ')} {...props} />
);
export const TabsTrigger: React.FC<{value:string} & React.ButtonHTMLAttributes<HTMLButtonElement>> = ({value, className='', children}) => {
  const {value:cur, setValue} = useContext(TabsCtx);
  const active = cur===value;
  return <button onClick={()=>setValue(value)} className={['px-3 py-1 rounded-lg text-sm', active?'bg-black text-white':'hover:bg-zinc-100', className].join(' ')}>{children}</button>;
};
export const TabsContent: React.FC<{value:string, children:any}> = ({value, children}) => {
  const {value:cur} = useContext(TabsCtx);
  return cur===value ? <div className="mt-3">{children}</div> : null;
};
