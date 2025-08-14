
import React from 'react';
export const Dialog: React.FC<{open:boolean, onOpenChange:(b:boolean)=>void, children:any}> = ({open, children}) => open ? <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">{children}</div> : null;
export const DialogContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({className='', ...props}) => <div className={['w-full max-w-xl rounded-2xl bg-white p-4 shadow-xl', className].join(' ')} {...props}/>;
export const DialogHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <div className="mb-2" {...props}/>;
export const DialogTitle: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <h3 className="text-lg font-semibold" {...props}/>;
