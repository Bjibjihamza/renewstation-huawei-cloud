import { LucideIcon } from 'lucide-react';

interface CardHeaderProps {
  icon: LucideIcon;
  title: string;
}

const CardHeader = ({ icon: Icon, title }: CardHeaderProps) => (
  <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
    <div className="p-2 rounded-lg" style={{ backgroundColor: '#FFF5F5' }}>
      <Icon className="w-5 h-5" style={{ color: '#FC0D1B' }} />
    </div>
    <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
  </div>
);

export default CardHeader;
