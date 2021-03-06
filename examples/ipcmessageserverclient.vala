/* 
 * Author: Jiří Janoušek <janousek.jiri@gmail.com>
 *
 * To the extent possible under law, author has waived all
 * copyright and related or neighboring rights to this file.
 * http://creativecommons.org/publicdomain/zero/1.0/
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

Diorite.Ipc.MessageServer server;

void main(string[] args)
{
	Diorite.Logger.init(stderr, GLib.LogLevelFlags.LEVEL_DEBUG);
	
	server = null;
	
	var thread = new Thread<void*>("server", run_server);
	message("Sleep");
	Thread.usleep(1*1000000);
	
	const string HELLO_WORLD = "Hello world";
	var variant = new Variant.string(HELLO_WORLD);
	var client = new Diorite.Ipc.MessageClient("test", 5000);
	
	try
	{
		var response = client.send_message("echo2", variant);
		message("Response: %s", response.get_string());
		assert(response.get_string() == HELLO_WORLD);
	}
	catch (Diorite.Ipc.MessageError e)
	{
		critical("Client error: %s".printf(e.message));
	}
	
	try
	{
		client.send_message("failing", variant);
	}
	catch (Diorite.Ipc.MessageError e)
	{
		message("Client error: %s".printf(e.message));
	}
	
	try
	{
		client.send_message("check_type", variant);
	}
	catch (Diorite.Ipc.MessageError e)
	{
		message("Client error: %s".printf(e.message));
	}
	
	try
	{
		client.send_message("check_type_null", variant);
	}
	catch (Diorite.Ipc.MessageError e)
	{
		message("Client error: %s".printf(e.message));
	}
	
	message("Stop server");
	try
	{
		server.stop();
	}
	catch (Diorite.IOError e)
	{
		critical("Server error: %s", e.message);
	}
	thread.join();
	
}

private void* run_server()
{
	server = new Diorite.Ipc.MessageServer("test");
	server.add_handler("echo2", echo_handler);
	server.add_handler("failing", failing_handler);
	server.add_handler("check_type", check_type_handler);
	server.add_handler("check_type_null", check_type_null_handler);
	try
	{
		message("Start server");
		server.listen();
		message("Server has ended");
	}
	catch (Diorite.IOError e)
	{
		critical("Server error: %s", e.message);
	}
	return null;
}

private Variant? echo_handler(Diorite.Ipc.MessageServer server, Variant? request) throws Diorite.Ipc.MessageError
{
	return request;
}

private Variant? failing_handler(Diorite.Ipc.MessageServer server, Variant? request) throws Diorite.Ipc.MessageError
{
	throw new Diorite.Ipc.MessageError.INVALID_ARGUMENTS("Bad type signature, dude!");
	return null;
}

private Variant? check_type_handler(Diorite.Ipc.MessageServer server, Variant? request) throws Diorite.Ipc.MessageError
{
	Diorite.Ipc.MessageServer.check_type_str(request, "(sisi)");
	return null;
}

private Variant? check_type_null_handler(Diorite.Ipc.MessageServer server, Variant? request) throws Diorite.Ipc.MessageError
{
	Diorite.Ipc.MessageServer.check_type_str(request, null);
	return null;
}
