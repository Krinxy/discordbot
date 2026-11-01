import { ExportButton } from "@/components/export-button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getTransferSummary } from "@/lib/admin-api";

export async function TransferPanel() {
  const summary = await getTransferSummary();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between rounded-2xl border border-border/60 p-4">
        <p className="text-sm">
          <span className="text-mono-tabular font-semibold">{summary.open_count}</span> open request(s)
          waiting to be exported.
        </p>
        <ExportButton />
      </div>
      {summary.requests.length > 0 && (
        <div className="overflow-x-auto rounded-2xl border border-border/60">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Payload</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary.requests.map((request) => (
                <TableRow key={request.id}>
                  <TableCell className="font-medium">{request.type}</TableCell>
                  <TableCell className="max-w-xs truncate">{request.payload}</TableCell>
                  <TableCell className="text-mono-tabular text-muted-foreground">
                    {new Date(request.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
