export function getErrorMessage(error) {
  if (error?.response?.status === 413) {
    return "Upload is too large for this deployment. On Vercel, direct uploads to the API must stay under about 4 MB total.";
  }

  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }
  return detail || error?.message || "Something went wrong";
}
