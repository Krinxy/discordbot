import { redirect } from "next/navigation";

export default function LogsRedirectPage() {
  redirect("/services/system_logs");
}
