
import React from 'react';
export const Separator: React.FC<{orientation?:'horizontal'|'vertical', className?:string}> = ({orientation='horizontal', className=''}) => (
  <div className={[orientation==='vertical'?'w-px h-full':'h-px w-full','bg-zinc-200', className].join(' ')} />
);
