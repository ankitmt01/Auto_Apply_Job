
import React from 'react';
export const Progress: React.FC<{value:number}> = ({value}) => (
  <div className="h-2 w-full rounded-full bg-zinc-200">
    <div className="h-2 rounded-full bg-black" style={{width: `${value}%`}} />
  </div>
);
