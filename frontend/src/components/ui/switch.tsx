
import React from 'react';
export const Switch: React.FC<{checked:boolean, onCheckedChange:(b:boolean)=>void}> = ({checked, onCheckedChange}) => (
  <label className="inline-flex cursor-pointer items-center gap-2">
    <input type="checkbox" className="peer hidden" checked={checked} onChange={(e)=>onCheckedChange(e.target.checked)} />
    <span className="h-5 w-9 rounded-full bg-zinc-300 peer-checked:bg-black relative transition-all">
      <span className="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-all peer-checked:translate-x-4"/>
    </span>
  </label>
);
