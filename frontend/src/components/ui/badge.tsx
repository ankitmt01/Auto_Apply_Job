
import React from 'react';
export const Badge: React.FC<{variant?:'secondary'|'outline', className?:string}> = ({variant='secondary', className='', children}) => {
  const base = 'inline-flex items-center rounded-full px-2.5 py-1 text-xs';
  const v = variant==='outline' ? 'border border-zinc-300 text-zinc-700' : 'bg-zinc-100 text-zinc-800';
  return <span className={[base, v, className].join(' ')}>{children}</span>;
};
