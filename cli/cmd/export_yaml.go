package cmd

import (
	"fmt"
	"os"
	"time"

	"agent-workbench/cli/internal/api"
	"agent-workbench/cli/internal/render"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"go.yaml.in/yaml/v3"
)

var exportYamlCmd = &cobra.Command{
	Use:   "yaml",
	Short: "Export project and tasks as a structured YAML snapshot",
	Long: `Generate a YAML file containing the project metadata and all tasks.

AWB remains the source of truth. This file is a portable snapshot useful for
offline review, onboarding collaborators, or feeding downstream tooling.

Example:
  awb export yaml
  awb export yaml --output my-project-snapshot.yaml`,
	RunE: func(cmd *cobra.Command, args []string) error {
		slug, err := requireFlag(cmd, "project")
		if err != nil {
			return err
		}

		output, _ := cmd.Flags().GetString("output")
		if output == "" {
			output = slug + "-export.yaml"
		}

		client := newClient()
		project, err := client.ProjectBySlug(slug)
		if err != nil {
			return render.Err("resolve project: %v", err)
		}

		tasks, err := listAllTasks(client, project.ID)
		if err != nil {
			return render.Err("list tasks: %v", err)
		}

		doc := buildYAMLExport(project, tasks, viper.GetString("api_url"))

		data, err := yaml.Marshal(doc)
		if err != nil {
			return render.Err("marshal YAML: %v", err)
		}

		if output == "-" {
			fmt.Print(string(data))
			return nil
		}
		if err := os.WriteFile(output, data, 0o644); err != nil {
			return render.Err("write file: %v", err)
		}
		render.Line("wrote %s (%d tasks)", output, len(tasks))
		return nil
	},
}

func init() {
	exportCmd.AddCommand(exportYamlCmd)
	exportYamlCmd.Flags().String("output", "", "Output file path (default: <slug>-export.yaml; use - for stdout)")
}

// exportDoc is the top-level YAML document structure.
type exportDoc struct {
	ExportedAt string         `yaml:"exported_at"`
	Source     string         `yaml:"source"`
	Project    exportProject  `yaml:"project"`
	Tasks      []exportTask   `yaml:"tasks"`
}

type exportProject struct {
	ID           string  `yaml:"id"`
	Name         string  `yaml:"name"`
	Slug         string  `yaml:"slug"`
	Type         string  `yaml:"type"`
	Environment  string  `yaml:"environment"`
	GitRemoteURL *string `yaml:"git_remote_url,omitempty"`
	LocalPath    *string `yaml:"local_path,omitempty"`
	DefaultAgent *string `yaml:"default_agent,omitempty"`
}

type exportTask struct {
	ID                       string  `yaml:"id"`
	Title                    string  `yaml:"title"`
	Status                   string  `yaml:"status"`
	Phase                    string  `yaml:"phase"`
	Priority                 int     `yaml:"priority"`
	Role                     *string `yaml:"role,omitempty"`
	ModelTier                *string `yaml:"model_tier,omitempty"`
	Description              *string `yaml:"description,omitempty"`
	ValidationExpectations   *string `yaml:"validation_expectations,omitempty"`
	CompletionEvidence       *string `yaml:"completion_evidence,omitempty"`
	EstimatedDurationSeconds *int    `yaml:"estimated_duration_seconds,omitempty"`
	AssigneeType             *string `yaml:"assignee_type,omitempty"`
	AssigneeName             *string `yaml:"assignee_name,omitempty"`
	ClaimedBy                *string `yaml:"claimed_by,omitempty"`
	CreatedAt                string  `yaml:"created_at"`
	UpdatedAt                string  `yaml:"updated_at"`
}

func buildYAMLExport(project api.Project, tasks []api.Task, apiURL string) exportDoc {
	doc := exportDoc{
		ExportedAt: time.Now().UTC().Format(time.RFC3339),
		Source:     apiURL,
		Project: exportProject{
			ID:           project.ID,
			Name:         project.Name,
			Slug:         project.Slug,
			Type:         project.ProjectType,
			Environment:  project.Environment,
			GitRemoteURL: project.GitRemoteURL,
			LocalPath:    project.LocalPath,
			DefaultAgent: project.DefaultAgent,
		},
	}

	for _, t := range tasks {
		doc.Tasks = append(doc.Tasks, exportTask{
			ID:                       t.ID,
			Title:                    t.Title,
			Status:                   t.Status,
			Phase:                    t.Phase,
			Priority:                 t.Priority,
			Role:                     t.Role,
			ModelTier:                t.ModelTier,
			Description:              t.Description,
			ValidationExpectations:   t.ValidationExpectations,
			CompletionEvidence:       t.CompletionEvidence,
			EstimatedDurationSeconds: t.EstimatedDurationSeconds,
			AssigneeType:             t.AssigneeType,
			AssigneeName:             t.AssigneeName,
			ClaimedBy:                t.ClaimedBy,
			CreatedAt:                t.CreatedAt,
			UpdatedAt:                t.UpdatedAt,
		})
	}
	return doc
}
