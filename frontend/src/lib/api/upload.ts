import type { JobResponse } from "@/types/api";

export const uploadApi = {
  uploadFile: async (file: File): Promise<JobResponse> => {
    const apiKey = localStorage.getItem("scout_api_key");
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/api/upload", {
      method: "POST",
      headers: {
        ...(apiKey ? { "X-API-Key": apiKey } : {}),
      },
      body: formData,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || "Upload failed");
    }

    return res.json();
  },
};
