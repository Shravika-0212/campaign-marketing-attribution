import React, { useEffect, useState } from 'react';
import {
  Search,
  User,
  Clock,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { fetchContacts, fetchCustomerJourney } from '../services/api';
import { ContactItem, CustomerJourney, JourneyEvent } from '../types';

interface JourneyPageProps {
  customerOnly?: boolean;
  isReadOnly?: boolean;
  contactIdOverride?: string;
}

export const JourneyPage: React.FC<JourneyPageProps> = ({
  customerOnly = false,
  isReadOnly = false,
  contactIdOverride
}) => {
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [selectedContactId, setSelectedContactId] = useState<string>('');
  const [journey, setJourney] = useState<CustomerJourney | null>(null);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (customerOnly && contactIdOverride) {
      setSelectedContactId(contactIdOverride);
      loadJourney(contactIdOverride);
    } else {
      // Load initial contacts list
      fetchContacts().then((data) => {
        setContacts(data);
        if (data.length > 0) {
          const targetId = contactIdOverride || data[0].contact_id;
          setSelectedContactId(targetId);
          loadJourney(targetId);
        }
      });
    }
  }, [customerOnly, contactIdOverride]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim() || customerOnly) return;
    const res = await fetchContacts(search);
    setContacts(res);
    if (res.length > 0) {
      setSelectedContactId(res[0].contact_id);
      loadJourney(res[0].contact_id);
    }
  };

  const loadJourney = async (cid: string) => {
    setLoading(true);
    try {
      const data = await fetchCustomerJourney(cid);
      setJourney(data);
    } catch (err) {
      console.error('Failed to load customer journey', err);
    } finally {
      setLoading(false);
    }
  };

  const getEventBadge = (type: JourneyEvent['event_type']) => {
    switch (type) {
      case 'ORDER':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'OPPORTUNITY':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
      case 'LEAD':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'TOUCHPOINT':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'SESSION':
        return 'bg-slate-700/50 text-slate-300 border-slate-600';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Role Notice Banners */}
      {customerOnly && (
        <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/20 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">
                Welcome, {journey?.contact_name || 'Shravika Kavati'}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Here is your verified chronological journey, touchpoint interactions, and completed purchase receipts in Indian Rupees (₹).
              </p>
            </div>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Verified Customer
          </span>
        </div>
      )}

      {isReadOnly && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex items-center space-x-3 text-xs text-amber-300">
          <Lock className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <span className="font-bold">Support Agent (Read-Only Mode):</span> You have read-only permissions to inspect customer profiles, sessions, and chronological events to resolve customer inquiries. Data mutation actions are locked.
          </div>
        </div>
      )}

      {/* Top Search & Contact Selector (Hidden in Customer View) */}
      {!customerOnly && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearch} className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search contact ID (e.g. CON-2026-000001) or email..."
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
            />
          </form>

          {/* Quick Contact Chips */}
          <div className="flex items-center space-x-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            <span className="text-[11px] text-slate-400 font-mono shrink-0">Sample Contacts:</span>
            {contacts.slice(0, 5).map((ct) => (
              <button
                key={ct.contact_id}
                onClick={() => {
                  setSelectedContactId(ct.contact_id);
                  loadJourney(ct.contact_id);
                }}
                className={`px-2.5 py-1 rounded text-[11px] font-mono transition shrink-0 ${
                  selectedContactId === ct.contact_id
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {ct.name ? `${ct.name} (${ct.contact_id})` : ct.contact_id}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Layout */}
      {journey && (
        <div className="space-y-6">
          {/* Customer Profile Banner */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400">
                <User className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-white">{journey.contact_name}</h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-emerald-400">
                    {journey.contact_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{journey.email}</p>
              </div>
            </div>

            <div className="flex items-center space-x-6 text-xs font-mono">
              <div>
                <span className="text-slate-400 block text-[10px]">LIFECYCLE STAGE</span>
                <span className="text-emerald-400 font-bold uppercase">{journey.lifecycle_stage}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">TOTAL EVENTS</span>
                <span className="text-white font-bold">{journey.total_events} Records</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">FIRST OBSERVED</span>
                <span className="text-slate-300">{new Date(journey.first_seen_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Interactive Chronological Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <div>
                <h4 className="text-sm font-semibold text-white">Chronological Journey Progression</h4>
                <p className="text-xs text-slate-400">Step-by-step audit of marketing touchpoints, sessions, and conversions</p>
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Ordered by Event Timestamp &rarr;
              </div>
            </div>

            {loading ? (
              <div className="py-16 text-center text-slate-400">Loading timeline...</div>
            ) : journey.events.length === 0 ? (
              <div className="py-16 text-center text-slate-400">No events found for this contact.</div>
            ) : (
              <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {journey.events.map((evt, idx) => {
                  const dateStr = new Date(evt.timestamp).toLocaleString();
                  return (
                    <div key={evt.event_id + idx} className="relative group">
                      {/* Timeline dot */}
                      <div className={`absolute -left-[27px] top-1.5 w-3.5 h-3.5 rounded-full border-2 ${
                        evt.event_type === 'ORDER' ? 'bg-emerald-400 border-emerald-950' : 'bg-slate-700 border-slate-900 group-hover:bg-slate-500'
                      }`} />

                      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-slate-700 transition">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1.5">
                          <div className="flex items-center space-x-2">
                            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${getEventBadge(evt.event_type)}`}>
                              {evt.event_type}
                            </span>
                            <span className="text-xs font-semibold text-white">{evt.title}</span>
                            {evt.is_anomaly && (
                              <span className="inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                <ShieldAlert className="w-3 h-3 mr-1" />
                                Quarantined Duplicate
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] font-mono text-slate-400 flex items-center">
                            <Clock className="w-3 h-3 mr-1 text-slate-500" />
                            {dateStr}
                          </span>
                        </div>

                        <p className="text-xs text-slate-300 mt-1">{evt.description}</p>

                        {/* Metadata Footer */}
                        <div className="mt-3 pt-2 border-t border-slate-900 flex flex-wrap items-center gap-3 text-[11px] font-mono text-slate-400">
                          <span className="text-slate-500">ID: {evt.event_id}</span>
                          {evt.campaign_id && (
                            <span className="text-emerald-400">Campaign: {evt.campaign_id}</span>
                          )}
                          {evt.channel && (
                            <span className="text-indigo-400">Channel: {evt.channel}</span>
                          )}
                          {evt.amount !== undefined && evt.amount !== null && (
                            <span className="text-amber-300 font-bold">Amount: ₹{evt.amount.toLocaleString('en-IN')}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
