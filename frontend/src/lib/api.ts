const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let sid = localStorage.getItem("datavera_session_id");
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem("datavera_session_id", sid);
  }
  return sid;
}

export function setSessionId(sid: string): void {
  if (typeof window !== "undefined" && sid) {
    localStorage.setItem("datavera_session_id", sid);
  }
}

export interface ColumnProfile {
  name: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  sample_values: any[];
  stats?: {
    min?: number;
    max?: number;
    avg?: number;
    stddev?: number;
    median?: number;
  };
}

export interface DatasetProfile {
  filename: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  sample_rows: Record<string, any>[];
  table_name: string;
}

export interface UploadResponse {
  session_id: string;
  message: string;
  profile: DatasetProfile;
  confidence_score: number;
  requires_user_action: boolean;
  detected_header_index: number;
  selected_sheet?: string;
  available_sheets: string[];
  warnings: string[];
  raw_preview_rows: any[][];
}

export interface SampleDatasetInfo {
  id: string;
  title: string;
  description: string;
  filename: string;
  row_count: number;
  column_count: number;
}

export interface ChatMessageResponse {
  question: string;
  sql: string;
  explanation: string;
  results: Record<string, any>[];
  columns: string[];
  row_count: number;
  chart_recommended: boolean;
  chart_type?: 'bar' | 'line' | 'pie' | 'scatter' | 'table';
  chart_options?: Record<string, any>;
  error?: string;
}

export async function uploadFile(
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const sessionId = getSessionId();
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/upload`);
    xhr.setRequestHeader("x-session-id", sessionId);

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data: UploadResponse = JSON.parse(xhr.responseText);
          if (data.session_id) setSessionId(data.session_id);
          resolve(data);
        } catch (e) {
          reject(new Error("Erreur de format de réponse du serveur."));
        }
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          reject(new Error(errData.detail || "Erreur lors du téléchargement du fichier."));
        } catch (e) {
          reject(new Error(`Erreur HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error("Erreur réseau lors de l'envoi du fichier."));
    xhr.send(formData);
  });
}

export async function reconfigureIngestion(
  config: { sheet_name?: string; header_index?: number; delimiter?: string }
): Promise<UploadResponse> {
  const sessionId = getSessionId();
  const res = await fetch(`${API_BASE_URL}/api/upload/configure`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-session-id": sessionId,
    },
    body: JSON.stringify(config),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Erreur lors de la reconfiguration de l'importation.");
  }
  const data: UploadResponse = await res.json();
  if (data.session_id) setSessionId(data.session_id);
  return data;
}

export async function fetchSampleDatasets(): Promise<SampleDatasetInfo[]> {
  const res = await fetch(`${API_BASE_URL}/api/samples`);
  if (!res.ok) throw new Error("Impossible de charger la liste des échantillons.");
  return res.json();
}

export async function loadSampleDataset(sampleId: string): Promise<UploadResponse> {
  const sessionId = getSessionId();
  const res = await fetch(`${API_BASE_URL}/api/samples/${sampleId}`, {
    method: "POST",
    headers: {
      "x-session-id": sessionId,
    },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Erreur lors du chargement de l'échantillon.");
  }
  const data: UploadResponse = await res.json();
  if (data.session_id) setSessionId(data.session_id);
  return data;
}

export async function sendChatMessage(
  question: string,
  provider?: string
): Promise<ChatMessageResponse> {
  const sessionId = getSessionId();
  const res = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-session-id": sessionId,
    },
    body: JSON.stringify({ question, provider }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Erreur lors du traitement de votre question.");
  }
  return res.json();
}
