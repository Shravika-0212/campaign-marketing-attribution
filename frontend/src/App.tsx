import React, { useEffect, useState } from 'react';
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
import { fetchAuthMe, fetchAvailableActors, setActiveRole, getActiveRole } from './services/api';
import { ActorProfile, UserRole } from './types';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [syncKey, setSyncKey] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // RBAC State
  const [currentActor, setCurrentActor] = useState<ActorProfile | null>(null);
  const [availableActors, setAvailableActors] = useState<ActorProfile[]>([]);

  useEffect(() => {
    loadRbacActors();
  }, []);

  const loadRbacActors = async () => {
    try {
      const [me, actors] = await Promise.all([
        fetchAuthMe(),
        fetchAvailableActors()
      ]);
      setCurrentActor(me);
      setAvailableActors(actors);

      // If active page is not permitted for loaded role, switch to first allowed page
      if (!me.allowed_pages.includes(activePage)) {
        setActivePage(me.allowed_pages[0] as PageId);
      }
    } catch (err) {
      console.error('Failed to load RBAC actors', err);
    }
  };

  const handleSelectActor = (actor: ActorProfile) => {
    setActiveRole(actor.role, actor.user_id);
    setCurrentActor(actor);

    // If current page is forbidden for new role, switch immediately to first permitted page
    if (!actor.allowed_pages.includes(activePage)) {
      setActivePage(actor.allowed_pages[0] as PageId);
    }

    // Force re-render of components with new credentials
    setSyncKey((prev) => prev + 1);
  };

  const pageHeaders: Record<PageId, { title: string; subtitle: string }> = {
    overview: {
      title: 'Executive Marketing Attribution & ROI Dashboard',
      subtitle: 'Real-time performance across First-Touch, Last-Touch, and Multi-Touch attribution models'
    },
    campaigns: {
      title: currentActor?.role === 'SUPPORT_AGENT'
        ? 'Campaign & Promotion Directory (Support Read-Only)'
        : 'Campaign Performance & Lifecycle Management',
      subtitle: currentActor?.role === 'SUPPORT_AGENT'
        ? 'Customer support lookup for active campaigns, channel tags, and promotional details'
        : 'Explore campaigns, track budgets vs actual spend, and inspect attributed conversions'
    },
    journey: {
      title: currentActor?.role === 'CUSTOMER_PROSPECT'
        ? 'My Customer Journey & Purchase Timeline'
        : currentActor?.role === 'SUPPORT_AGENT'
        ? 'Customer Profile & Interaction History (Support Read-Only)'
        : 'Customer Journey Explorer & Timeline Audit',
      subtitle: currentActor?.role === 'CUSTOMER_PROSPECT'
        ? 'Trace your personal touchpoints, web sessions, and completed order receipts in ₹ INR'
        : currentActor?.role === 'SUPPORT_AGENT'
        ? 'Read-only chronological customer timeline for inquiry resolution and audit'
        : 'Trace individual prospect touchpoints, web sessions, leads, and orders chronologically'
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
      subtitle: 'Reproducible generation across STARTER and FULL scales with 15 validation rules (System Admin)'
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

  const isPagePermitted = currentActor ? currentActor.allowed_pages.includes(activePage) : true;

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onSelectPage={setActivePage}
        datasetScale="STARTER"
        currentActor={currentActor}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          title={pageHeaders[activePage]?.title || 'Marketing Attribution Platform'}
          subtitle={pageHeaders[activePage]?.subtitle}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          currentActor={currentActor}
          availableActors={availableActors}
          onSelectActor={handleSelectActor}
        />

        <main key={syncKey} className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {!isPagePermitted && currentActor ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 max-w-lg mx-auto text-center space-y-4 my-12">
              <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto text-rose-400">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Access Denied (403 Forbidden)</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Your current role <span className="text-rose-400 font-mono font-semibold">{currentActor.role_name}</span> does not have permissions to access this view.
                </p>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg text-left text-xs font-mono text-slate-400">
                <div>Required Permission: <span className="text-amber-400">Restricted Dashboard</span></div>
                <div>Your Assigned Pages: <span className="text-emerald-400">{currentActor.allowed_pages.join(', ')}</span></div>
              </div>
              <button
                onClick={() => setActivePage(currentActor.allowed_pages[0] as PageId)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 text-xs font-bold transition"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Return to Allowed View ({currentActor.allowed_pages[0]})</span>
              </button>
            </div>
          ) : (
            <>
              {activePage === 'overview' && <OverviewPage />}
              {activePage === 'campaigns' && <CampaignsPage isReadOnly={currentActor?.role === 'SUPPORT_AGENT'} />}
              {activePage === 'journey' && (
                <JourneyPage
                  customerOnly={currentActor?.role === 'CUSTOMER_PROSPECT'}
                  isReadOnly={currentActor?.role === 'SUPPORT_AGENT'}
                  contactIdOverride={currentActor?.contact_id || undefined}
                />
              )}
              {activePage === 'attribution' && <AttributionPage />}
              {activePage === 'roi' && <RoiPage />}
              {activePage === 'anomalies' && <AnomaliesPage />}
              {activePage === 'generator' && <GeneratorPage />}
              {activePage === 'reports' && <ReportsPage />}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
