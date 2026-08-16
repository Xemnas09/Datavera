"use client";

import React, { useState, useRef, useEffect } from "react";
import { sendChatMessage, ChatMessageResponse } from "@/lib/api";
import { EChartViewer } from "./EChartViewer";
import { DataTable } from "./DataTable";
import {
  Send,
  Sparkles,
  Code,
  CheckCircle2,
  AlertCircle,
  BarChart,
  Table as TableIcon,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Bot,
  User
} from "lucide-react";

interface MessageItem {
  id: string;
  sender: "user" | "assistant";
  text: string;
  response?: ChatMessageResponse;
  loading?: boolean;
}

interface ChatInterfaceProps {
  datasetName?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ datasetName }) => {
  const [inputQuestion, setInputQuestion] = useState("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSqlIds, setExpandedSqlIds] = useState<Record<string, boolean>>({});
  const chatEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    "Affiche un résumé synthétique des données",
    "Quelles sont les valeurs principales et les totaux ?",
    "Affiche la répartition par catégorie sous forme de graphique",
    "Donne-moi le top 5 des éléments les plus représentés",
  ];

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleSqlExpand = (id: string) => {
    setExpandedSqlIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async (questionText?: string) => {
    const textToSend = (questionText || inputQuestion).trim();
    if (!textToSend || loading) return;

    setInputQuestion("");
    const userMsgId = crypto.randomUUID();
    const botMsgId = crypto.randomUUID();

    const newMessages: MessageItem[] = [
      ...messages,
      { id: userMsgId, sender: "user", text: textToSend },
      { id: botMsgId, sender: "assistant", text: textToSend, loading: true },
    ];

    setMessages(newMessages);
    setLoading(true);

    try {
      const res = await sendChatMessage(textToSend);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? { ...msg, loading: false, response: res }
            : msg
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? {
                ...msg,
                loading: false,
                response: {
                  question: textToSend,
                  sql: "",
                  explanation: "",
                  results: [],
                  columns: [],
                  row_count: 0,
                  chart_recommended: false,
                  error: err.message || "Erreur lors du traitement de la requête.",
                },
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col h-[700px] overflow-hidden">
      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-sky-600 to-indigo-600 text-white rounded-xl">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">Assistant IA & Moteur DuckDB</h3>
            <p className="text-xs text-slate-500">
              Posez une question en français — Génération de SQL transparent & graphiques
            </p>
          </div>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-slate-50/30">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 max-w-lg mx-auto py-8">
            <div className="p-4 bg-sky-50 text-sky-600 rounded-2xl">
              <MessageSquare className="w-10 h-10" />
            </div>
            <div>
              <h4 className="font-bold text-slate-800 text-lg">Que voulez-vous savoir ?</h4>
              <p className="text-sm text-slate-500 mt-1">
                L'assistant analyse votre jeu de données <span className="font-semibold text-slate-700">{datasetName || "importé"}</span> via des requêtes DuckDB SQL sécurisées.
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="w-full space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Exemples de questions
              </span>
              <div className="grid gap-2 text-left">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="p-3 text-xs sm:text-sm font-medium text-slate-700 bg-white border border-slate-200 hover:border-sky-300 hover:bg-sky-50/50 rounded-xl transition-all shadow-sm flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-4 h-4 text-slate-400 group-hover:text-sky-600 transition-colors" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="space-y-3">
              {/* User Bubble */}
              {msg.sender === "user" ? (
                <div className="flex items-start justify-end space-x-2">
                  <div className="bg-sky-600 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-lg shadow-sm text-sm">
                    {msg.text}
                  </div>
                  <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                </div>
              ) : (
                /* Assistant Bubble */
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                    <Bot className="w-4 h-4" />
                  </div>

                  <div className="flex-1 space-y-4 max-w-3xl">
                    {msg.loading ? (
                      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm inline-flex items-center space-x-3 text-slate-600 text-sm">
                        <div className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                        <span>Génération de la requête DuckDB SQL & analyse...</span>
                      </div>
                    ) : msg.response?.error ? (
                      <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-4 text-sm flex items-start space-x-3">
                        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold block">Erreur d'analyse :</span>
                          <span>{msg.response.error}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 text-slate-800">
                        {/* Explanation */}
                        {msg.response?.explanation && (
                          <p className="text-sm font-medium text-slate-800">
                            {msg.response.explanation}
                          </p>
                        )}

                        {/* Transparency SQL Dropdown */}
                        {msg.response?.sql && (
                          <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50">
                            <button
                              onClick={() => toggleSqlExpand(msg.id)}
                              className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-mono text-slate-700 hover:bg-slate-100 transition-colors"
                            >
                              <div className="flex items-center space-x-2">
                                <Code className="w-4 h-4 text-sky-600" />
                                <span className="font-semibold text-slate-900">Requête DuckDB SQL exécutée</span>
                              </div>
                              {expandedSqlIds[msg.id] ? (
                                <ChevronUp className="w-4 h-4 text-slate-500" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-slate-500" />
                              )}
                            </button>

                            {expandedSqlIds[msg.id] && (
                              <div className="p-4 bg-slate-900 text-slate-100 text-xs font-mono overflow-x-auto border-t border-slate-200">
                                <pre>{msg.response.sql}</pre>
                              </div>
                            )}
                          </div>
                        )}

                        {/* ECharts Visualization */}
                        {msg.response?.chart_recommended && msg.response?.chart_options && (
                          <div className="pt-2">
                            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 mb-2">
                              <BarChart className="w-4 h-4 text-indigo-600" />
                              <span>Visualisation graphique ({msg.response.chart_type})</span>
                            </div>
                            <EChartViewer options={msg.response.chart_options} />
                          </div>
                        )}

                        {/* Data Table */}
                        {msg.response?.results && msg.response.results.length > 0 && (
                          <div className="pt-2">
                            <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-2">
                              <div className="flex items-center space-x-2">
                                <TableIcon className="w-4 h-4 text-sky-600" />
                                <span>Résultats ({msg.response.row_count} lignes)</span>
                              </div>
                            </div>
                            <DataTable
                              columns={msg.response.columns}
                              data={msg.response.results}
                              pageSize={5}
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="Posez votre question sur le jeu de données..."
            disabled={loading}
            className="flex-1 px-4 py-3 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent disabled:bg-slate-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || !inputQuestion.trim()}
            className="px-5 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-xl font-medium text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-2 shadow-sm"
          >
            <span>Envoyer</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
