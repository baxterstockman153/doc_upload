import ActivityLogTable from "@/components/ActivityLogTable";

export default function LogsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Activity Logs</h1>
      <ActivityLogTable />
    </div>
  );
}
