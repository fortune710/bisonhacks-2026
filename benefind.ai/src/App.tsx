/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import {
  Search,
  MapPin,
  Users,
  DollarSign,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Building2,
  ShoppingBasket,
  ExternalLink,
  Navigation,
  Car,
  Train,
  ChevronLeft,
  Info,
  Mic
} from 'lucide-react';
import Markdown from 'react-markdown';
import { checkEligibility, getSnapResources } from './services/geminiService';

const STATES = [
  "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
  "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
  "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
  "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
  "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
];

type Step = 'landing' | 'location' | 'household' | 'results';

export default function App() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('landing');
  const [formData, setFormData] = useState({
    state: '',
    zipcode: '',
    familySize: 1,
    income: 0
  });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{
    eligibility: any;
    resources: any;
  } | null>(null);

  const handleNext = () => {
    if (step === 'landing') setStep('location');
    else if (step === 'location') setStep('household');
    else if (step === 'household') fetchResults();
  };

  const handleBack = () => {
    if (step === 'location') setStep('landing');
    else if (step === 'household') setStep('location');
    else if (step === 'results') setStep('household');
  };

  const fetchResults = async () => {
    setLoading(true);
    try {
      const eligibility = await checkEligibility(formData.familySize, formData.income, formData.state);
      const resources = await getSnapResources(formData.zipcode, formData.state);

      // Parse sections
      const text = resources.text || '';
      const officeMatch = text.match(/\[SNAP_OFFICE\]([\s\S]*?)(?=\[GROCERY_STORES\]|\[FOOD_PANTRIES\]|$)/);
      const storesMatch = text.match(/\[GROCERY_STORES\]([\s\S]*?)(?=\[SNAP_OFFICE\]|\[FOOD_PANTRIES\]|$)/);
      const pantriesMatch = text.match(/\[FOOD_PANTRIES\]([\s\S]*?)(?=\[SNAP_OFFICE\]|\[GROCERY_STORES\]|$)/);

      const parsedResources = {
        office: officeMatch ? officeMatch[1].trim() : '',
        stores: storesMatch ? storesMatch[1].trim() : '',
        pantries: pantriesMatch ? pantriesMatch[1].trim() : '',
        fullText: text,
        groundingChunks: resources.groundingChunks
      };

      setResults({ eligibility, resources: parsedResources });
      setStep('results');
    } catch (error) {
      console.error(error);
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fdfcfb] text-slate-900 font-sans selection:bg-emerald-100">
      {/* Header */}
      <header className="border-b border-slate-100 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => setStep('landing')}
          >
            <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
              <ShoppingBasket className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-800">benefind<span className="text-emerald-600">.ai</span></span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-500">
            {/* Links moved to footer */}
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        <AnimatePresence mode="wait">
          {step === 'landing' && (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center py-12 md:py-24"
            >
              <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900 mb-6">
                Food is a <br />
                <span className="text-emerald-600 italic font-serif">basic human right.</span>
              </h1>
              <p className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
                Check your SNAP eligibility in minutes and find local resources to help you and your family thrive.
              </p>
              <button
                onClick={handleNext}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-4 rounded-2xl font-semibold text-lg shadow-lg shadow-emerald-200 transition-all hover:scale-105 flex items-center gap-2 mx-auto"
              >
                Check Eligibility <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => navigate('/agent')}
                className="bg-white hover:bg-slate-50 text-slate-900 px-8 py-4 rounded-2xl font-semibold text-lg shadow-lg shadow-slate-200/50 transition-all hover:scale-105 flex items-center gap-2 mx-auto border border-slate-200"
              >
                Talk to AI Assistant <Mic className="w-5 h-5" />
              </button>

              <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
                {[
                  { icon: CheckCircle2, title: "Quick Check", desc: "Answer a few simple questions to see if you qualify for SNAP benefits." },
                  { icon: MapPin, title: "Local Offices", desc: "Find the nearest SNAP office and get directions from your current location." },
                  { icon: ShoppingBasket, title: "Smart Shopping", desc: "Discover budget-friendly stores nearby that accept EBT payments." }
                ].map((feature, i) => (
                  <div key={i} className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm">
                    <feature.icon className="w-10 h-10 text-emerald-600 mb-4" />
                    <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                    <p className="text-slate-500 leading-relaxed">{feature.desc}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {step === 'location' && (
            <motion.div
              key="location"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="max-w-xl mx-auto"
            >
              <button onClick={handleBack} className="flex items-center gap-1 text-slate-400 hover:text-slate-600 mb-8 transition-colors">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <h2 className="text-3xl font-bold mb-2">Where are you located?</h2>
              <p className="text-slate-500 mb-8">We use this to find local offices and stores near you.</p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wider">State</label>
                  <select
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    className="w-full bg-white border border-slate-200 rounded-2xl px-4 py-4 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all appearance-none"
                  >
                    <option value="">Select your state</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wider">Zipcode</label>
                  <div className="relative">
                    <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="e.g. 90210"
                      value={formData.zipcode}
                      onChange={(e) => setFormData({ ...formData, zipcode: e.target.value })}
                      className="w-full bg-white border border-slate-200 rounded-2xl pl-12 pr-4 py-4 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                    />
                  </div>
                </div>
                <button
                  disabled={!formData.state || formData.zipcode.length < 5}
                  onClick={handleNext}
                  className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white py-4 rounded-2xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  Continue <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}

          {step === 'household' && (
            <motion.div
              key="household"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="max-w-xl mx-auto"
            >
              <button onClick={handleBack} className="flex items-center gap-1 text-slate-400 hover:text-slate-600 mb-8 transition-colors">
                <ChevronLeft className="w-4 h-4" /> Back
              </button>
              <h2 className="text-3xl font-bold mb-2">Tell us about your household</h2>
              <p className="text-slate-500 mb-8">This information helps us estimate your eligibility.</p>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wider">Family Size</label>
                  <div className="relative">
                    <Users className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                    <input
                      type="number"
                      min="1"
                      value={formData.familySize}
                      onChange={(e) => setFormData({ ...formData, familySize: parseInt(e.target.value) || 1 })}
                      className="w-full bg-white border border-slate-200 rounded-2xl pl-12 pr-4 py-4 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wider">Monthly Gross Income</label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                    <input
                      type="number"
                      placeholder="0.00"
                      value={formData.income || ''}
                      onChange={(e) => setFormData({ ...formData, income: parseFloat(e.target.value) || 0 })}
                      className="w-full bg-white border border-slate-200 rounded-2xl pl-12 pr-4 py-4 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                    />
                  </div>
                  <p className="mt-2 text-xs text-slate-400 flex items-center gap-1">
                    <Info className="w-3 h-3" /> Income before taxes and deductions.
                  </p>
                </div>
                <button
                  disabled={loading}
                  onClick={handleNext}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-200 text-white py-4 rounded-2xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  {loading ? "Calculating..." : "See Results"} <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}

          {step === 'results' && results && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-12"
            >
              <div className="flex items-center justify-between">
                <button onClick={handleBack} className="flex items-center gap-1 text-slate-400 hover:text-slate-600 transition-colors">
                  <ChevronLeft className="w-4 h-4" /> Edit Info
                </button>
                <div className="text-xs font-mono text-slate-400 uppercase tracking-widest">Results for {formData.zipcode}</div>
              </div>

              {/* Eligibility Card */}
              <div className={`p-8 rounded-[2rem] border ${results.eligibility.isEligible ? 'bg-emerald-50 border-emerald-100' : 'bg-rose-50 border-rose-100'}`}>
                <div className="flex flex-col md:flex-row gap-6 items-start">
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shrink-0 ${results.eligibility.isEligible ? 'bg-emerald-600' : 'bg-rose-600'}`}>
                    {results.eligibility.isEligible ? <CheckCircle2 className="text-white w-10 h-10" /> : <XCircle className="text-white w-10 h-10" />}
                  </div>
                  <div>
                    <h2 className="text-3xl font-bold mb-2">
                      {results.eligibility.isEligible ? "You may be eligible!" : "You might not qualify."}
                    </h2>
                    <p className="text-slate-600 leading-relaxed max-w-2xl">
                      {results.eligibility.reason}
                    </p>
                    <div className="mt-6 flex flex-wrap gap-4">
                      <a
                        href={`https://www.fns.usda.gov/snap/state-directory`}
                        target="_blank"
                        rel="noreferrer"
                        className="bg-slate-900 text-white px-6 py-3 rounded-xl text-sm font-semibold flex items-center gap-2 hover:bg-slate-800 transition-all"
                      >
                        Apply in {formData.state} <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Local Resources */}
                <div className="lg:col-span-2 space-y-8">
                  <section>
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                      <Building2 className="text-emerald-600" /> Local SNAP Offices & Stores
                    </h3>
                    <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm prose prose-slate max-w-none">
                      {results.resources.office && (
                        <div className="mb-8">
                          <h4 className="text-lg font-bold text-emerald-700 mb-4">Closest SNAP Office</h4>
                          <Markdown>{results.resources.office}</Markdown>
                        </div>
                      )}

                      {results.resources.stores && (
                        <div>
                          <h4 className="text-lg font-bold text-emerald-700 mb-4">Budget-Friendly Grocery Stores</h4>
                          <Markdown>{results.resources.stores}</Markdown>
                        </div>
                      )}

                      {!results.resources.office && !results.resources.stores && (
                        <Markdown>{results.resources.fullText}</Markdown>
                      )}

                      {results.resources.groundingChunks.length > 0 && (
                        <div className="mt-8 pt-8 border-t border-slate-100">
                          <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Verified Sources</h4>
                          <div className="flex flex-wrap gap-3">
                            {results.resources.groundingChunks.map((chunk: any, i: number) => (
                              chunk.web && (
                                <a
                                  key={i}
                                  href={chunk.web.uri}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg text-xs font-medium text-slate-600 transition-colors"
                                >
                                  {chunk.web.title} <ExternalLink className="w-3 h-3" />
                                </a>
                              )
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </section>

                  {/* Transportation */}
                  <section>
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                      <Navigation className="text-emerald-600" /> Getting There
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-start gap-4">
                        <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
                          <Car className="text-blue-600 w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-bold mb-1">Rideshare Estimate</h4>
                          <p className="text-sm text-slate-500 mb-3">Estimated Uber/Lyft cost to nearest office.</p>
                          <span className="text-lg font-mono font-bold text-slate-900">$12 - $18</span>
                        </div>
                      </div>
                      <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-start gap-4">
                        <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0">
                          <Train className="text-indigo-600 w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-bold mb-1">Public Transit</h4>
                          <p className="text-sm text-slate-500 mb-3">Check local metro or bus schedules.</p>
                          <a href="https://www.google.com/maps/dir/?api=1&destination=SNAP+Office" target="_blank" rel="noreferrer" className="text-sm text-emerald-600 font-semibold hover:underline">View on Maps</a>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>

                {/* Sidebar Resources */}
                <div className="space-y-8">
                  <section>
                    <h3 className="text-xl font-bold mb-6">Local Support</h3>
                    <div className="space-y-4">
                      <div className="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 bg-orange-50 rounded-xl flex items-center justify-center">
                            <ShoppingBasket className="text-orange-600 w-5 h-5" />
                          </div>
                          <span className="font-bold text-lg">Food Pantries</span>
                        </div>
                        {results.resources.pantries ? (
                          <div className="prose prose-sm prose-slate max-w-none">
                            <Markdown>{results.resources.pantries}</Markdown>
                          </div>
                        ) : (
                          <p className="text-sm text-slate-500">Searching for local pantries and their hours...</p>
                        )}
                      </div>
                    </div>
                  </section>

                  <div className="bg-emerald-900 text-white p-8 rounded-[2rem] relative overflow-hidden">
                    <div className="relative z-10">
                      <h4 className="text-xl font-bold mb-4">Need immediate help?</h4>
                      <p className="text-emerald-100 text-sm mb-6 leading-relaxed">
                        If you are in a crisis, please call the National Hunger Hotline.
                      </p>
                      <a href="tel:1-866-348-6479" className="block w-full text-center bg-white text-emerald-900 py-3 rounded-xl font-bold hover:bg-emerald-50 transition-colors">
                        1-866-3-HUNGRY
                      </a>
                    </div>
                    <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-emerald-800 rounded-full blur-3xl opacity-50" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="border-t border-slate-100 py-12 mt-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-6 h-6 bg-emerald-600 rounded flex items-center justify-center">
                  <ShoppingBasket className="text-white w-4 h-4" />
                </div>
                <span className="font-bold text-slate-800">benefind.ai</span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed max-w-sm">
                Empowering communities with easy access to food security resources and SNAP eligibility information.
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-slate-900">National Resources</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><a href="https://www.feedingamerica.org" target="_blank" rel="noreferrer" className="hover:text-emerald-600 transition-colors">Feeding America</a></li>
                <li><a href="https://www.toogoodtogo.com" target="_blank" rel="noreferrer" className="hover:text-emerald-600 transition-colors">Too Good To Go</a></li>
                <li><a href="https://www.fns.usda.gov/snap" target="_blank" rel="noreferrer" className="hover:text-emerald-600 transition-colors">USDA SNAP Official</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4 text-slate-900">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-500">
                <li><a href="#" className="hover:text-emerald-600 transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-emerald-600 transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-100 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-slate-400 text-center md:text-left">
              &copy; 2024 benefind.ai. This is an informational tool and not an official government application.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
