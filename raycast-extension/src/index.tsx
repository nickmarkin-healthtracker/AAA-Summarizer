import {
  Action,
  ActionPanel,
  Form,
  Icon,
  List,
  showToast,
  Toast,
  useNavigation,
  LocalStorage,
  Color,
} from "@raycast/api";
import { useState, useEffect } from "react";
import { exec } from "child_process";
import { promisify } from "util";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";

const execAsync = promisify(exec);

// Path to the Python project
const PROJECT_PATH = "/Users/nmarkin/Library/CloudStorage/Dropbox/Claude Code Projects/AAA Summarizer";

interface Faculty {
  name: string;
  email: string;
  quarters: string;
  points: number;
  status: string;
}


// Run Python CLI command
async function runPythonCommand(args: string): Promise<string> {
  // Use the virtual environment Python for PDF support
  const command = `cd "${PROJECT_PATH}" && source venv/bin/activate && python3 -m src.cli ${args}`;
  try {
    const { stdout, stderr } = await execAsync(command, {
      maxBuffer: 10 * 1024 * 1024,
      env: { ...process.env, PATH: "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" }
    });
    if (stderr && !stderr.includes("Warning")) {
      console.error("stderr:", stderr);
    }
    return stdout;
  } catch (error: unknown) {
    const err = error as Error & { stderr?: string };
    throw new Error(err.stderr || err.message);
  }
}

// Parse faculty list from CLI output (JSON mode)
async function getFacultyList(csvPath: string): Promise<Faculty[]> {
  const output = await runPythonCommand(`list-faculty "${csvPath}" --json`);
  try {
    return JSON.parse(output);
  } catch {
    // Fallback: parse table output
    const lines = output.split("\n");
    const faculty: Faculty[] = [];
    for (const line of lines) {
      const match = line.match(/│\s*\d+\s*│\s*([^│]+)│\s*([^│]+)│\s*([^│]+)│\s*([\d,]+)\s*│\s*([^│]+)│/);
      if (match) {
        faculty.push({
          name: match[1].trim(),
          email: match[2].trim(),
          quarters: match[3].trim(),
          points: parseInt(match[4].replace(/,/g, "")),
          status: match[5].trim(),
        });
      }
    }
    return faculty;
  }
}


// Main menu component
export default function Command() {
  const [csvPath, setCsvPath] = useState<string>("");
  const { push } = useNavigation();

  useEffect(() => {
    // Load last used CSV path
    LocalStorage.getItem<string>("lastCsvPath").then((path) => {
      if (path) setCsvPath(path);
    });
  }, []);

  if (!csvPath) {
    return <SelectCSVForm onSelect={(path) => {
      setCsvPath(path);
      LocalStorage.setItem("lastCsvPath", path);
    }} />;
  }

  return (
    <List>
      <List.Section title="Academic Achievement Reports">
        <List.Item
          icon={Icon.Document}
          title="Export Points Summary (CSV)"
          subtitle="Export all faculty points to CSV file"
          actions={
            <ActionPanel>
              <Action
                title="Export Points"
                onAction={() => push(<ExportPoints csvPath={csvPath} />)}
              />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.Person}
          title="Generate Individual Summaries"
          subtitle="Select faculty members and export PDF summaries"
          actions={
            <ActionPanel>
              <Action
                title="Select Faculty"
                onAction={() => push(<SelectFaculty csvPath={csvPath} />)}
              />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.List}
          title="Generate Activity Reports"
          subtitle="Select activity types and export PDF reports"
          actions={
            <ActionPanel>
              <Action
                title="Select Activities"
                onAction={() => push(<SelectActivities csvPath={csvPath} />)}
              />
            </ActionPanel>
          }
        />
      </List.Section>
      <List.Section title="Data Source">
        <List.Item
          icon={Icon.Folder}
          title="Change CSV File"
          subtitle={csvPath.split("/").pop()}
          accessories={[{ text: "Current file" }]}
          actions={
            <ActionPanel>
              <Action
                title="Select Different CSV"
                onAction={() => {
                  setCsvPath("");
                }}
              />
            </ActionPanel>
          }
        />
      </List.Section>
    </List>
  );
}

// CSV file selection form
function SelectCSVForm({ onSelect }: { onSelect: (path: string) => void }) {
  const [csvPath, setCsvPath] = useState<string[]>([]);

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Use This CSV"
            onSubmit={(values) => {
              if (values.csvFile && values.csvFile.length > 0) {
                onSelect(values.csvFile[0]);
              }
            }}
          />
        </ActionPanel>
      }
    >
      <Form.FilePicker
        id="csvFile"
        title="Select REDCap CSV Export"
        allowMultipleSelection={false}
        canChooseDirectories={false}
        canChooseFiles={true}
      />
      <Form.Description
        title="Note"
        text="Select the REDCap CSV export file with labeled headers"
      />
    </Form>
  );
}

// Export Points component
function ExportPoints({ csvPath }: { csvPath: string }) {
  const [isLoading, setIsLoading] = useState(false);

  async function handleExport(values: { outputDir: string[] }) {
    setIsLoading(true);
    try {
      const outputDir = values.outputDir?.[0] || path.join(os.homedir(), "Desktop");
      const outputFile = path.join(outputDir, "points_summary.csv");

      await showToast({ style: Toast.Style.Animated, title: "Exporting points..." });
      await runPythonCommand(`points "${csvPath}" -o "${outputFile}"`);

      await showToast({
        style: Toast.Style.Success,
        title: "Points exported!",
        message: outputFile,
        primaryAction: {
          title: "Open in Finder",
          onAction: () => exec(`open "${outputDir}"`),
        },
      });
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Export failed",
        message: String(error),
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Form
      isLoading={isLoading}
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Export Points CSV" onSubmit={handleExport} />
        </ActionPanel>
      }
    >
      <Form.Description
        title="Export Points Summary"
        text="This will generate a CSV file with all faculty members and their point totals, sorted alphabetically by surname."
      />
      <Form.FilePicker
        id="outputDir"
        title="Save Location"
        allowMultipleSelection={false}
        canChooseDirectories={true}
        canChooseFiles={false}
        defaultValue={[path.join(os.homedir(), "Desktop")]}
      />
    </Form>
  );
}

// Faculty selection component
function SelectFaculty({ csvPath }: { csvPath: string }) {
  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const { push } = useNavigation();

  useEffect(() => {
    getFacultyList(csvPath)
      .then(setFaculty)
      .catch((error) => {
        showToast({ style: Toast.Style.Failure, title: "Error loading faculty", message: String(error) });
      })
      .finally(() => setIsLoading(false));
  }, [csvPath]);

  function toggleSelection(email: string) {
    const newSelected = new Set(selected);
    if (newSelected.has(email)) {
      newSelected.delete(email);
    } else {
      newSelected.add(email);
    }
    setSelected(newSelected);
  }

  function selectAll() {
    setSelected(new Set(faculty.map((f) => f.email)));
  }

  function deselectAll() {
    setSelected(new Set());
  }

  return (
    <List isLoading={isLoading}>
      <List.Section title="Actions">
        <List.Item
          icon={Icon.CheckCircle}
          title="Select All"
          accessories={[{ text: `${faculty.length} faculty` }]}
          actions={
            <ActionPanel>
              <Action title="Select All" onAction={selectAll} />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.Circle}
          title="Deselect All"
          actions={
            <ActionPanel>
              <Action title="Deselect All" onAction={deselectAll} />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.Download}
          title="Export Selected"
          accessories={[{ text: selected.size > 0 ? `${selected.size} selected` : "none selected" }]}
          actions={
            <ActionPanel>
              <Action
                title="Export Selected"
                onAction={() => {
                  if (selected.size === 0) {
                    showToast({ style: Toast.Style.Failure, title: "No faculty selected" });
                    return;
                  }
                  push(<ExportFacultySummaries csvPath={csvPath} selectedEmails={Array.from(selected)} />);
                }}
              />
            </ActionPanel>
          }
        />
      </List.Section>
      <List.Section title={`Faculty (${selected.size} of ${faculty.length} selected)`}>
        {faculty.map((f) => (
          <List.Item
            key={f.email}
            icon={selected.has(f.email) ? Icon.CheckCircle : Icon.Circle}
            title={f.name}
            subtitle={f.email}
            accessories={[
              { text: `${f.points.toLocaleString()} pts` },
              { tag: f.status === "INCOMPLETE" ? { value: "INCOMPLETE", color: Color.Red } : { value: "Complete", color: Color.Green } },
            ]}
            actions={
              <ActionPanel>
                <Action
                  title={selected.has(f.email) ? "Deselect" : "Select"}
                  onAction={() => toggleSelection(f.email)}
                />
                <Action title="Select All" onAction={selectAll} />
                <Action title="Deselect All" onAction={deselectAll} />
                <Action
                  title="Export Selected"
                  onAction={() => {
                    if (selected.size === 0) {
                      showToast({ style: Toast.Style.Failure, title: "No faculty selected" });
                      return;
                    }
                    push(<ExportFacultySummaries csvPath={csvPath} selectedEmails={Array.from(selected)} />);
                  }}
                />
              </ActionPanel>
            }
          />
        ))}
      </List.Section>
    </List>
  );
}

// Export faculty summaries form
function ExportFacultySummaries({ csvPath, selectedEmails }: { csvPath: string; selectedEmails: string[] }) {
  const [isLoading, setIsLoading] = useState(false);

  async function handleExport(values: { outputDir: string[]; format: string; combined: boolean }) {
    setIsLoading(true);
    try {
      const outputDir = values.outputDir?.[0] || path.join(os.homedir(), "Desktop");
      const format = values.format || "pdf";
      const combined = values.combined;

      await showToast({ style: Toast.Style.Animated, title: "Generating summaries..." });

      const facultyArgs = selectedEmails.map((e) => `-f "${e}"`).join(" ");
      const formatArg = `-F ${format}`;

      const combinedArg = combined ? "--combined" : "";
      await runPythonCommand(`summary "${csvPath}" ${facultyArgs} -o "${outputDir}" ${formatArg} ${combinedArg}`);

      const message = combined
        ? `${selectedEmails.length} faculty combined`
        : `${selectedEmails.length} individual files`;

      await showToast({
        style: Toast.Style.Success,
        title: "Summaries exported!",
        message: message,
        primaryAction: {
          title: "Open in Finder",
          onAction: () => exec(`open "${outputDir}"`),
        },
      });
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Export failed",
        message: String(error),
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Form
      isLoading={isLoading}
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Export Summaries" onSubmit={handleExport} />
        </ActionPanel>
      }
    >
      <Form.Description
        title="Export Faculty Summaries"
        text={`Exporting summaries for ${selectedEmails.length} faculty member(s)`}
      />
      <Form.FilePicker
        id="outputDir"
        title="Save Location"
        allowMultipleSelection={false}
        canChooseDirectories={true}
        canChooseFiles={false}
        defaultValue={[path.join(os.homedir(), "Desktop")]}
      />
      <Form.Dropdown id="format" title="Format" defaultValue="pdf">
        <Form.Dropdown.Item value="pdf" title="PDF" />
        <Form.Dropdown.Item value="md" title="Markdown" />
        <Form.Dropdown.Item value="both" title="Both PDF and Markdown" />
      </Form.Dropdown>
      <Form.Checkbox
        id="combined"
        label="Combine into single document"
        defaultValue={false}
      />
    </Form>
  );
}

// Activity selection component
function SelectActivities({ csvPath }: { csvPath: string }) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const { push } = useNavigation();

  // Activity type mapping
  const activityTypes: { key: string; name: string; category: string }[] = [
    { key: "citizenship.evaluations", name: "Trainee Evaluation Completion", category: "Citizenship" },
    { key: "citizenship.committees", name: "Committee Membership", category: "Citizenship" },
    { key: "citizenship.department_activities", name: "Department Citizenship Activities", category: "Citizenship" },
    { key: "education.teaching_awards", name: "Teaching Awards & Recognition", category: "Education" },
    { key: "education.lectures", name: "Lectures & Curriculum", category: "Education" },
    { key: "education.board_prep", name: "Board Preparation Activities", category: "Education" },
    { key: "education.mentorship", name: "Trainee Mentorship", category: "Education" },
    { key: "education.feedback", name: "MyTIPreport & MTR", category: "Education" },
    { key: "research.grant_review", name: "Grant Review (NIH Study Section)", category: "Research" },
    { key: "research.grant_awards", name: "Grant Awards", category: "Research" },
    { key: "research.grant_submissions", name: "Grant Submissions", category: "Research" },
    { key: "research.thesis_committees", name: "Thesis/Dissertation Committees", category: "Research" },
    { key: "leadership.education_leadership", name: "Education Leadership", category: "Leadership" },
    { key: "leadership.society_leadership", name: "Society Leadership", category: "Leadership" },
    { key: "leadership.board_leadership", name: "Board Examination Leadership", category: "Leadership" },
    { key: "content_expert.speaking", name: "Invited Speaking", category: "Content Expert" },
    { key: "content_expert.publications_peer", name: "Peer-Reviewed Publications", category: "Content Expert" },
    { key: "content_expert.publications_nonpeer", name: "Non-Peer-Reviewed Publications", category: "Content Expert" },
    { key: "content_expert.pathways", name: "Clinical Pathways", category: "Content Expert" },
    { key: "content_expert.textbooks", name: "Textbook Contributions", category: "Content Expert" },
    { key: "content_expert.abstracts", name: "Research Abstracts", category: "Content Expert" },
    { key: "content_expert.journal_editorial", name: "Journal Editorial Roles", category: "Content Expert" },
  ];


  function toggleSelection(key: string) {
    const newSelected = new Set(selected);
    if (newSelected.has(key)) {
      newSelected.delete(key);
    } else {
      newSelected.add(key);
    }
    setSelected(newSelected);
  }

  function selectAll() {
    setSelected(new Set(activityTypes.map((a) => a.key)));
  }

  function deselectAll() {
    setSelected(new Set());
  }

  // Group by category
  const categories = ["Citizenship", "Education", "Research", "Leadership", "Content Expert"];

  return (
    <List isLoading={isLoading}>
      <List.Section title="Actions">
        <List.Item
          icon={Icon.CheckCircle}
          title="Select All"
          accessories={[{ text: `${activityTypes.length} activities` }]}
          actions={
            <ActionPanel>
              <Action title="Select All" onAction={selectAll} />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.Circle}
          title="Deselect All"
          actions={
            <ActionPanel>
              <Action title="Deselect All" onAction={deselectAll} />
            </ActionPanel>
          }
        />
        <List.Item
          icon={Icon.Download}
          title="Export Selected"
          accessories={[{ text: selected.size > 0 ? `${selected.size} selected` : "none selected" }]}
          actions={
            <ActionPanel>
              <Action
                title="Export Selected"
                onAction={() => {
                  if (selected.size === 0) {
                    showToast({ style: Toast.Style.Failure, title: "No activities selected" });
                    return;
                  }
                  push(<ExportActivityReports csvPath={csvPath} selectedActivities={Array.from(selected)} />);
                }}
              />
            </ActionPanel>
          }
        />
      </List.Section>
      {categories.map((category) => (
        <List.Section key={category} title={`${category} (${activityTypes.filter(a => a.category === category && selected.has(a.key)).length}/${activityTypes.filter(a => a.category === category).length})`}>
          {activityTypes
            .filter((a) => a.category === category)
            .map((a) => (
              <List.Item
                key={a.key}
                icon={selected.has(a.key) ? Icon.CheckCircle : Icon.Circle}
                title={a.name}
                actions={
                  <ActionPanel>
                    <Action
                      title={selected.has(a.key) ? "Deselect" : "Select"}
                      onAction={() => toggleSelection(a.key)}
                    />
                    <Action title="Select All" onAction={selectAll} />
                    <Action title="Deselect All" onAction={deselectAll} />
                    <Action
                      title="Export Selected"
                      onAction={() => {
                        if (selected.size === 0) {
                          showToast({ style: Toast.Style.Failure, title: "No activities selected" });
                          return;
                        }
                        push(<ExportActivityReports csvPath={csvPath} selectedActivities={Array.from(selected)} />);
                      }}
                    />
                  </ActionPanel>
                }
              />
            ))}
        </List.Section>
      ))}
    </List>
  );
}

// Export activity reports form
function ExportActivityReports({ csvPath, selectedActivities }: { csvPath: string; selectedActivities: string[] }) {
  const [isLoading, setIsLoading] = useState(false);

  async function handleExport(values: { outputDir: string[]; format: string; sortBy: string }) {
    setIsLoading(true);
    try {
      const outputDir = values.outputDir?.[0] || path.join(os.homedir(), "Desktop");
      const format = values.format || "pdf";
      const sortBy = values.sortBy || "faculty";

      await showToast({ style: Toast.Style.Animated, title: "Generating activity reports..." });

      const activityArgs = selectedActivities.map((a) => `-t "${a}"`).join(" ");
      const formatArg = `-F ${format}`;
      const sortArg = `-s ${sortBy}`;

      await runPythonCommand(`activity "${csvPath}" ${activityArgs} -o "${outputDir}" ${formatArg} ${sortArg}`);

      await showToast({
        style: Toast.Style.Success,
        title: "Reports generated!",
        message: `${selectedActivities.length} activity type(s) exported`,
        primaryAction: {
          title: "Open in Finder",
          onAction: () => exec(`open "${outputDir}"`),
        },
      });
    } catch (error) {
      await showToast({
        style: Toast.Style.Failure,
        title: "Export failed",
        message: String(error),
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Form
      isLoading={isLoading}
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Export Reports" onSubmit={handleExport} />
        </ActionPanel>
      }
    >
      <Form.Description
        title="Export Activity Reports"
        text={`Exporting ${selectedActivities.length} activity type(s)`}
      />
      <Form.FilePicker
        id="outputDir"
        title="Save Location"
        allowMultipleSelection={false}
        canChooseDirectories={true}
        canChooseFiles={false}
        defaultValue={[path.join(os.homedir(), "Desktop")]}
      />
      <Form.Dropdown id="format" title="Format" defaultValue="pdf">
        <Form.Dropdown.Item value="pdf" title="PDF" />
        <Form.Dropdown.Item value="md" title="Markdown" />
        <Form.Dropdown.Item value="both" title="Both PDF and Markdown" />
      </Form.Dropdown>
      <Form.Dropdown id="sortBy" title="Sort By" defaultValue="faculty">
        <Form.Dropdown.Item value="faculty" title="Faculty Name" />
        <Form.Dropdown.Item value="date" title="Date" />
        <Form.Dropdown.Item value="points" title="Points" />
      </Form.Dropdown>
    </Form>
  );
}
