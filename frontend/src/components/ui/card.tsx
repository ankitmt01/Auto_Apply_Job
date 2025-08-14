
import React from 'react';
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({className='', ...props}) => (
  <div className={['rounded-2xl border bg-white', className].join(' ')} {...props} />
);
export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({className='', ...props}) => (
  <div className={['p-4', className].join(' ')} {...props} />
);
