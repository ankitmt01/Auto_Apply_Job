
import React from 'react';
export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({className='', ...props}, ref) => (<input ref={ref} className={['w-full rounded-xl border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-zinc-300', className].join(' ')} {...props} />)
);
Input.displayName='Input';
