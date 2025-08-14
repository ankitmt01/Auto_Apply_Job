
import React from 'react';
export const TooltipProvider: React.FC<{children:any}> = ({children}) => <>{children}</>;
export const Tooltip: React.FC<{children:any}> = ({children}) => <>{children}</>;
export const TooltipTrigger: React.FC<{asChild?:boolean, children:any}> = ({children}) => <>{children}</>;
export const TooltipContent: React.FC<{children:any}> = ({children}) => <span className="ml-2 text-xs text-zinc-500">{children}</span>;
