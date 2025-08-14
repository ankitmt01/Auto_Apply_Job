
import React from 'react';
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'default'|'outline', size?: 'sm'|'md' };
export const Button: React.FC<Props> = ({ className='', variant='default', size='md', ...props }) => {
  const base = 'inline-flex items-center justify-center rounded-xl border transition px-3 py-2 text-sm';
  const v = variant==='outline' ? 'bg-white border-zinc-300 hover:bg-zinc-50' : 'bg-black text-white border-black hover:bg-zinc-800';
  const s = size==='sm' ? 'px-2 py-1 text-sm' : '';
  return <button className={[base,v,s,className].join(' ')} {...props} />;
};
export default Button;
