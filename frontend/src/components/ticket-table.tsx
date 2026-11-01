import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getTickets } from "@/lib/admin-api";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  open: "default",
  operation: "secondary",
  closed: "outline",
  archive: "outline",
  currently_not_possible: "destructive",
};

export async function TicketTable() {
  const tickets = await getTickets();

  if (tickets.length === 0) {
    return <p className="text-sm text-muted-foreground">No tickets yet.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-border/60">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Author</TableHead>
            <TableHead>Content</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tickets.map((ticket) => (
            <TableRow key={ticket.id}>
              <TableCell className="font-medium">{ticket.author}</TableCell>
              <TableCell className="max-w-xs truncate">{ticket.content}</TableCell>
              <TableCell>
                <Badge variant={statusVariant[ticket.status] ?? "outline"}>{ticket.status}</Badge>
              </TableCell>
              <TableCell className="text-mono-tabular text-muted-foreground">
                {new Date(ticket.created_at).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
