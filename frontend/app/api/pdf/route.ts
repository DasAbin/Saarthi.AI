import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink } from "fs/promises";
import { exec } from "child_process";
import util from "util";
import path from "path";
import os from "os";

const execPromise = util.promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      console.error("No file provided in the request.");
      return NextResponse.json(
        { success: false, message: "No file provided" },
        { status: 400 }
      );
    }

    // Verify file upload handled correctly (multipart/form-data)
    console.log(`Received file: ${file.name}, type: ${file.type}, size: ${file.size} bytes`);

    const buffer = Buffer.from(await file.arrayBuffer());

    // Save them temporarily to /tmp
    const tmpDir = os.tmpdir();
    const tempFilePath = path.join(tmpDir, `upload-${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.]/g, '_')}`);

    try {
      await writeFile(tempFilePath, buffer);
      console.log(`File temporarily saved to ${tempFilePath}`);
    } catch (fsError) {
      console.error("Failed to save file to /tmp:", fsError);
      return NextResponse.json(
        { success: false, message: "Failed to save file to server" },
        { status: 500 }
      );
    }

    const pyScriptPath = path.join(process.cwd(), "app", "api", "pdf", "extract.py");

    try {
      console.log(`Extracting text by executing python script...`);
      // Spawning the python script with tempFilePath and internal filename
      const { stdout, stderr } = await execPromise(`python "${pyScriptPath}" "${tempFilePath}" "${file.name}"`);

      if (stderr) {
        console.warn(`Python stderr non-empty (might be warnings): ${stderr}`);
      }

      let result;
      try {
        result = JSON.parse(stdout);
      } catch (parseError) {
        console.error("Failed to parse python output:", stdout);
        console.error("Python stderr was:", stderr);
        throw new Error("Invalid output from processing script");
      }

      if (!result.success) {
        throw new Error(result.message || "Unknown error occurred during document extraction");
      }

      // Cleanup
      await unlink(tempFilePath).catch(e => console.error("Failed to cleanup temp file:", e));

      console.log("Document processing successful, returning extracted text and summary.");
      return NextResponse.json({
        success: true,
        data: {
          extracted_text: result.extracted_text,
          summary: result.summary,
        },
      });

    } catch (execError: any) {
      console.error("Execution error during python script:", execError);
      // Cleanup on error
      await unlink(tempFilePath).catch(e => console.error("Failed to cleanup temp file:", e));

      return NextResponse.json(
        { success: false, message: execError.message || "Failed to process document" },
        { status: 500 }
      );
    }

  } catch (error) {
    console.error("Unhandled API Route Error:", error);
    return NextResponse.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Internal error processing PDF",
      },
      { status: 500 }
    );
  }
}
