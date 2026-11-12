import React, { useState } from 'react';
import { Sidebar, PageId } from './components/Sidebar';
import { Header } from './components/Header';
import { OverviewPage } from './pages/OverviewPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { JourneyPage } from './pages/JourneyPage';
import { AttributionPage } from './pages/AttributionPage';
import { RoiPage } from './pages/RoiPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { GeneratorPage } from './pages/GeneratorPage';
import { ReportsPage } from './pages/ReportsPage';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [syncKey, setSyncKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const pageHeaders: Record<PageId, { title: string; subtitle: string }> = {
    overview: {
      title: 'Executive Marketing Attribution & ROI Dashboard',
      subtitle: 'Real-time performance across First-Touch, Last-Touch, and Multi-Touch attribution models'
    },
    campaigns: {
      title: 'Campaign Performance & Lifecycle Management',
      subtitle: 'Explore campaigns, track budgets vs actual spend, and inspect attributed conversions'
    },
    journey: {
      title: 'Customer Journey Explorer & Timeline Audit',
      subtitle: 'Trace individual prospect touchpoints, web sessions, leads, and orders chronologically'
    },
    attribution: {
      title: 'Multi-Model Marketing Attribution Analysis',
      subtitle: 'First-Touch vs Last-Touch vs Multi-Touch Linear with configurable lookback windows'
    },
    roi: {
      title: 'Marketing ROI & Unit Economics Analytics',
      subtitle: 'Evaluate return on media spend, CPL, CPA, and capital efficiency across channels'
    },
    anomalies: {
      title: 'Data Quality Assurance & Anomaly Detection',
      subtitle: 'Isolated 5 mandatory anomaly scenarios evaluated against ground truth precision and recall'
    },
    generator: {
      title: 'Deterministic Synthetic Data Generation Engine',
      subtitle: 'Reproducible generation across STARTER and FULL scales with 15 validation rules'
    },
    reports: {
      title: 'Data Exports, Relational Schema & Compliance Manifest',
      subtitle: 'Download CSV, JSON, SQL database seeds, data dictionary, and cryptographic manifests'
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setSyncKey((prev) => prev + 1);
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onSelectPage={setActivePage}
        datasetScale="STARTER"
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={pageHeaders[activePage].title}
          subtitle={pageHeaders[activePage].subtitle}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        <main key={syncKey} className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {activePage === 'overview' && <OverviewPage />}
          {activePage === 'campaigns' && <CampaignsPage />}
          {activePage === 'journey' && <JourneyPage />}
          {activePage === 'attribution' && <AttributionPage />}
          {activePage === 'roi' && <RoiPage />}
          {activePage === 'anomalies' && <AnomaliesPage />}
          {activePage === 'generator' && <GeneratorPage />}
          {activePage === 'reports' && <ReportsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
